import os
import re
import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class LlamaSummarizer:
    """
    Summarizes scientific articles using a Llama model via the Groq API.

    Uses LangChain's map-reduce summarization chain to handle potentially long texts.
    Extracts both a structured summary and key concepts.
    """

    def __init__(self, model_name: str = "llama3-8b-8192", temperature: float = 0.2):
        """
        Initializes the summarizer.

        Args:
            model_name (str): The name of the Llama model to use on Groq (e.g., "llama3-8b-8192", "llama3-70b-8192").
                                Check Groq's documentation for available models.
            temperature (float): The sampling temperature for the LLM (0.0 to 1.0). Lower values are more deterministic.

        Raises:
            ValueError: If the GROQ_API_KEY environment variable is not set.
        """
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY environment variable not set.")
            raise ValueError("GROQ_API_KEY must be set in environment variables")

        self.model_name = model_name
        self.temperature = temperature

        try:
            self.llm = ChatGroq(
                api_key=api_key,
                model=model_name, # Use 'model' parameter for ChatGroq
                temperature=temperature
            )
        except Exception as e:
            logging.error(f"Failed to initialize ChatGroq LLM: {e}")
            raise

        # --- Prompts for Summarization Chain ---

        # Map Prompt: Summarize individual chunks concisely
        self.map_prompt_template = """
        Based *only* on the following text snippet from a scientific article, write a very concise summary focusing on the key information presented:
        "{text}"
        CONCISE SUMMARY:
        """
        self.map_prompt = PromptTemplate.from_template(self.map_prompt_template)

        # Combine Prompt: Synthesize map results into a final structured summary + key concepts
        self.combine_prompt_template = """
        Your task is to synthesize intermediate summaries of a scientific article for a student audience.
        Create a comprehensive final summary structured in approximately 5 short paragraphs, clearly highlighting:
        1. The main research question or problem addressed.
        2. The core methodology or approach used by the researchers.
        3. The key findings and results reported.
        4. The significance or contribution of these results to the field.
        5. Potential implications, applications, or future directions mentioned.

        After the summary, provide a list of 5-7 essential key concepts or technical terms crucial for understanding the research.

        Use the following intermediate summaries as your source material:
        "{text}"

        Provide your output in the following format EXACTLY:
        FINAL SUMMARY:
        [Your comprehensive summary paragraphs here]

        KEY CONCEPTS:
        - Concept 1
        - Concept 2
        - ...
        """
        self.combine_prompt = PromptTemplate.from_template(self.combine_prompt_template)

        # --- Summarization Chain Setup ---
        try:
            self.chain = load_summarize_chain(
                self.llm,
                chain_type="map_reduce",
                map_prompt=self.map_prompt,
                combine_prompt=self.combine_prompt,
                verbose=True # Set to False in production if logs are too noisy
            )
        except Exception as e:
            logging.error(f"Failed to load summarization chain: {e}")
            raise

        # --- Text Splitter ---
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,  # Adjust based on model context window and typical article length
            chunk_overlap=200,
            length_function=len,
            add_start_index=True # Helpful for context if needed later
        )

    def _prepare_input_text(self, article_data: Dict[str, Any]) -> str:
        """Constructs the input text from article data."""
        text_parts = []
        if article_data.get('title'):
            text_parts.append(f"Title: {article_data['title']}")

        # Always include the abstract if available, it's crucial context
        if article_data.get('abstract'):
            text_parts.append(f"Abstract: {article_data['abstract']}")
        else:
             logging.warning("No abstract found in article data. Summary quality may be reduced.")

        # Use full text if provided, otherwise summary relies heavily on abstract/title
        full_text = article_data.get('full_text')
        if full_text:
            text_parts.append(f"Full Text:\n{full_text}")
            logging.info("Using full text for summarization.")
        else:
            logging.info("Full text not provided. Summarizing based on Title and Abstract.")

        return "\n\n".join(text_parts)

    def _parse_llm_output(self, llm_output: str) -> Dict[str, Any]:
        """Parses the structured output from the LLM."""
        summary = llm_output # Default if parsing fails
        key_concepts = []

        try:
            # Use regex to split based on the expected format, ignoring case
            # Looks for "FINAL SUMMARY:" and "KEY CONCEPTS:" as delimiters
            summary_match = re.search(r"FINAL SUMMARY:(.*?)KEY CONCEPTS:", llm_output, re.IGNORECASE | re.DOTALL)
            concepts_match = re.search(r"KEY CONCEPTS:(.*)", llm_output, re.IGNORECASE | re.DOTALL)

            if summary_match and concepts_match:
                summary = summary_match.group(1).strip()
                concepts_text = concepts_match.group(1).strip()

                # Extract concepts (handles lines starting with -, *, or number.)
                raw_concepts = re.findall(r"^\s*(?:[-*•]|\d+\.)\s*(.*?)\s*$", concepts_text, re.MULTILINE)
                key_concepts = [concept.strip() for concept in raw_concepts if concept.strip()]
            else:
                logging.warning("Could not parse LLM output using expected delimiters ('FINAL SUMMARY:', 'KEY CONCEPTS:'). Returning full output as summary.")
                # Attempt simpler split as fallback? Maybe not reliable enough.
                # Keep key_concepts empty if primary parsing failed.

        except Exception as e:
            logging.error(f"Error parsing LLM output: {e}. Returning raw output.")
            summary = llm_output # Ensure we still return the raw output on error
            key_concepts = []

        return {'summary': summary, 'key_concepts': key_concepts}


    def summarize(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarizes the provided article data.

        Args:
            article_data (Dict[str, Any]): A dictionary containing article information.
                                           Expected keys: 'abstract' (required for good summary).
                                           Optional keys: 'title', 'full_text'.

        Returns:
            Dict[str, Any]: A dictionary containing:
                            {'summary': str, 'key_concepts': List[str]}
                            Returns empty concepts list and potentially raw LLM output
                            as summary if parsing fails.
        """
        if not article_data or not article_data.get('abstract'):
             logging.warning("Summarizer called with missing or empty article data/abstract.")
             return {'summary': "Error: Insufficient article data provided for summarization.", 'key_concepts': []}

        input_text = self._prepare_input_text(article_data)

        if not input_text.strip():
            logging.warning("Prepared input text is empty.")
            return {'summary': "Error: No text content available for summarization.", 'key_concepts': []}

        # Split text into documents for the map-reduce chain
        texts = self.text_splitter.split_text(input_text)
        docs = [Document(page_content=t) for t in texts]

        logging.info(f"Summarizing using {len(docs)} document chunks.")

        try:
            # Run the summarization chain
            result = self.chain.invoke({"input_documents": docs})
            llm_output_text = result.get("output_text", "")

            if not llm_output_text:
                logging.error("Summarization chain returned empty output.")
                return {'summary': "Error: Summarization process failed to produce output.", 'key_concepts': []}

            # Parse the structured output
            parsed_output = self._parse_llm_output(llm_output_text)
            return parsed_output

        except Exception as e:
            logging.error(f"Error during summarization chain execution: {e}", exc_info=True) # Log traceback
            return {'summary': f"Error: Summarization failed due to an internal error ({type(e).__name__}).", 'key_concepts': []}


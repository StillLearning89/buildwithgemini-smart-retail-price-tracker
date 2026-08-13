import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-47433e0ab402"
LOCATION = "us-central1"
GCS_PATH = "gs://retail-price-tracker-qwiklabs-gcp-03-47433e0ab402/rag/retail_policies_and_perks_guide.txt"

PARSING_PROMPT = (
    "Extract all retail store price matching policies, return windows, membership perks, "
    "shipping rules, and unit price formulas described in this text. Omit metadata."
)

print(f"Initializing Vertex AI for project {PROJECT_ID} in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 1. Switch region RAG managed DB to serverless mode
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
print("Setting RAG managed DB mode to Serverless...")
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    )
)

# 2. Create the corpus
print("Creating serverless RAG corpus...")
corpus = rag.create_corpus(
    display_name="retail-policies-corpus",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print("CORPUS_NAME:", corpus.name)

# 3. Import + parse + chunk + embed
print(f"Importing and indexing {GCS_PATH} into corpus...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-2.5-flash",
        custom_parsing_prompt=PARSING_PROMPT,
    ),
)
print("IMPORTED_FILES_COUNT:", resp.imported_rag_files_count)

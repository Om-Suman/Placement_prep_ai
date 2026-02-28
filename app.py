import streamlit as st
from google import genai
from endee import Endee
import os
import requests

# ─── Load secrets (works both locally and on Streamlit Cloud) ──────────────────
def get_secret(key, default=""):
    # Try st.secrets first (Streamlit Cloud), then env vars (local)
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)

st.set_page_config(page_title="Placement Prep AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #4a9eff; }
    .subtitle   { font-size: 1.1rem; color: #aaa; margin-bottom: 1.5rem; }
    .chat-user  { background: #2a2d3e; color: #ffffff; border-radius: 12px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #4a9eff; }
    .chat-ai    { background: #1e2a1e; color: #ffffff; border-radius: 12px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #34a853; }
    .chat-user strong, .chat-ai strong { color: #ffffff; }
    .source-chip{ display: inline-block; background: #3a3000; color: #ffe082; border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; margin: 2px; }
    .status-ok  { color: #34a853; font-weight: 600; }
    .status-err { color: #ea4335; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

gemini_key  = get_secret("GEMINI_API_KEY")
# load Endee service URL/token
# default is empty; tests fallback to localhost inside functions later
endee_url   = get_secret("ENDEE_URL")
endee_token = get_secret("ENDEE_AUTH_TOKEN")

# ensure the URL includes a scheme, since users often paste just the hostname
if endee_url and not endee_url.startswith("http://") and not endee_url.startswith("https://"):
    endee_url = "https://" + endee_url

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    topics = ["All Topics", "DSA & Algorithms", "System Design", "OOPs & Design Patterns", "HR & Behavioural", "Company-Specific", "Core CS Subjects"]
    selected_topic = st.selectbox("Filter by topic", topics)
    st.divider()
    top_k        = st.slider("Retrieved chunks (top-k)", 1, 10, 5)
    show_sources = st.checkbox("Show source references", value=True)

INDEX_NAME = "placement_prep"

PLACEMENT_KB = [
    {"id": "dsa_001", "topic": "DSA & Algorithms", "question": "What is dynamic programming?", "answer": "Dynamic Programming (DP) is an algorithmic technique that solves complex problems by breaking them into overlapping subproblems and caching results (memoization/tabulation). Key patterns: 0/1 Knapsack, LCS, LIS, Coin Change, Matrix Chain Multiplication."},
    {"id": "dsa_002", "topic": "DSA & Algorithms", "question": "Explain BFS vs DFS", "answer": "BFS (Breadth-First Search) explores level by level using a queue - best for shortest paths. DFS (Depth-First Search) explores as deep as possible using a stack/recursion - best for cycle detection, topological sort, connected components."},
    {"id": "dsa_003", "topic": "DSA & Algorithms", "question": "What is time complexity of quicksort?", "answer": "QuickSort: Average O(n log n), Worst O(n2) when pivot is always min/max. Space: O(log n) average. Use randomised pivot to avoid worst case. Preferred over MergeSort for in-place sorting."},
    {"id": "dsa_004", "topic": "DSA & Algorithms", "question": "How does a HashMap work internally?", "answer": "HashMap uses an array of buckets. Key is hashed to compute index. Collision handled by chaining (LinkedList/Red-Black tree in Java 8+). Load factor default 0.75; rehashing doubles capacity. Average O(1) get/put, worst O(n) with collisions."},
    {"id": "dsa_005", "topic": "DSA & Algorithms", "question": "What is a sliding window technique?", "answer": "Sliding window maintains a subarray/substring of variable or fixed size by expanding and shrinking pointers. Used in: Maximum sum subarray of size k, Longest substring without repeating chars, Minimum window substring. Reduces O(n2) to O(n)."},
    {"id": "dsa_006", "topic": "DSA & Algorithms", "question": "Explain two-pointer technique", "answer": "Two pointers start at different positions (often both ends or both start) and move inward or outward. Classic use cases: Pair sum in sorted array, Remove duplicates in-place, Container with most water, Three-sum problem."},
    {"id": "sd_001", "topic": "System Design", "question": "How to design a URL shortener like bit.ly?", "answer": "Components: API server, Base62 encoding for short codes, SQL/NoSQL DB mapping short to long URL, Cache (Redis) for hot URLs, CDN for redirect speed. Scalability: consistent hashing, DB sharding by short-code prefix. Handle 301 vs 302 redirects."},
    {"id": "sd_002", "topic": "System Design", "question": "What is CAP theorem?", "answer": "CAP: Consistency (all nodes see same data), Availability (every request gets response), Partition Tolerance (works despite network splits). You can only guarantee 2 of 3. CP systems: HBase, Zookeeper. AP systems: Cassandra, DynamoDB."},
    {"id": "sd_003", "topic": "System Design", "question": "How to design Twitter's news feed?", "answer": "Fan-out on write: push tweets to follower feeds asynchronously. Fan-out on read: pull tweets at request time for celebrities (hybrid approach). Cache feeds in Redis. Use message queue (Kafka) for async processing. Timeline stored as list of tweet IDs."},
    {"id": "sd_004", "topic": "System Design", "question": "What is the difference between SQL and NoSQL?", "answer": "SQL: structured schema, ACID transactions, joins, vertical scaling. Best for financial apps, ERP. NoSQL: flexible schema, horizontal scaling, BASE properties. Types: Document (MongoDB), Key-Value (Redis), Column (Cassandra), Graph (Neo4j)."},
    {"id": "sd_005", "topic": "System Design", "question": "Explain load balancing strategies", "answer": "Round Robin: requests distributed equally. Least Connections: sent to server with fewest active connections. IP Hash: same client always hits same server. Weighted: more powerful servers get more requests. Health checks remove unhealthy servers automatically."},
    {"id": "oop_001", "topic": "OOPs & Design Patterns", "question": "What are SOLID principles?", "answer": "S - Single Responsibility: one class one job. O - Open/Closed: open for extension closed for modification. L - Liskov Substitution: subclass should substitute parent. I - Interface Segregation: small specific interfaces. D - Dependency Inversion: depend on abstractions not concretions."},
    {"id": "oop_002", "topic": "OOPs & Design Patterns", "question": "Explain Singleton design pattern", "answer": "Singleton ensures only one instance exists. Implementation: private constructor, static getInstance() method. Thread-safe version uses double-checked locking or enum. Use cases: DB connection pool, Logger, Configuration manager."},
    {"id": "oop_003", "topic": "OOPs & Design Patterns", "question": "What is polymorphism?", "answer": "Polymorphism allows same interface to be used for different underlying forms. Compile-time (overloading): same method name different params. Runtime (overriding): subclass provides specific implementation of parent method."},
    {"id": "oop_004", "topic": "OOPs & Design Patterns", "question": "What is the difference between abstract class and interface?", "answer": "Abstract class: can have concrete methods, constructor, state (fields). A class can extend only ONE abstract class. Interface: all methods abstract (Java 8+ allows default/static). A class can implement MULTIPLE interfaces."},
    {"id": "hr_001", "topic": "HR & Behavioural", "question": "Tell me about yourself", "answer": "Structure: Present (current role/education + key skills) then Past (relevant experience/projects) then Future (why this company/role). Keep it 90 seconds. Tailor to job description. End with enthusiasm for the specific opportunity."},
    {"id": "hr_002", "topic": "HR & Behavioural", "question": "What is your greatest weakness?", "answer": "Pick a REAL but non-critical weakness. Show self-awareness plus active improvement steps. Example: I sometimes over-engineer solutions; I have started setting timebox limits and asking for early feedback. Avoid cliche answers like I work too hard."},
    {"id": "hr_003", "topic": "HR & Behavioural", "question": "Why do you want to join this company?", "answer": "Research 3 things: company product/mission, recent news/growth, team culture. Structure: (1) Specific reason tied to company work, (2) How it aligns with your skills, (3) Your long-term fit. Avoid generic answers about salary/brand."},
    {"id": "hr_004", "topic": "HR & Behavioural", "question": "Describe a challenging project you worked on", "answer": "Use STAR method: Situation (context), Task (your responsibility), Action (specific steps you took - use I not we), Result (measurable outcome). Quantify impact: reduced load time by 40%, handled 10k concurrent users."},
    {"id": "co_001", "topic": "Company-Specific", "question": "Amazon leadership principles for interviews", "answer": "Key principles to prepare: Customer Obsession, Ownership, Invent and Simplify, Bias for Action, Deliver Results, Dive Deep, Earn Trust. For each have 2-3 STAR stories ready. Amazon uses LP-based behavioural questions in EVERY round."},
    {"id": "co_002", "topic": "Company-Specific", "question": "How is Google's hiring process structured?", "answer": "Google: 1 Phone screen (LC medium), 4-5 Onsite rounds (2 coding, 1 system design, 1 behavioural/Googleyness). Hiring committee reviews all feedback. Focus: problem-solving approach, communication, CS fundamentals. LC 150-200 problems recommended."},
    {"id": "cs_001", "topic": "Core CS Subjects", "question": "What is a deadlock and how to prevent it?", "answer": "Deadlock: 4 conditions must hold simultaneously - Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait. Prevention: Break any one condition. Strategies: Lock ordering (always acquire in same order), Lock timeout, Banker's algorithm."},
    {"id": "cs_002", "topic": "Core CS Subjects", "question": "Explain TCP vs UDP", "answer": "TCP: connection-oriented, reliable (ack + retransmit), ordered delivery, flow/congestion control. Use: HTTP, FTP, email. UDP: connectionless, no guarantee, fast, low overhead. Use: video streaming, DNS, gaming, VoIP. TCP handshake: SYN then SYN-ACK then ACK."},
    {"id": "cs_003", "topic": "Core CS Subjects", "question": "What is virtual memory?", "answer": "Virtual memory abstracts physical RAM using paging. Each process gets its own virtual address space. OS maps virtual pages to physical frames via page table. Page fault triggers swap-in from disk. Benefits: process isolation, run programs larger than RAM."},
]

EMBED_MODELS = ["models/text-embedding-004", "models/embedding-001", "models/text-multilingual-embedding-002"]

def get_embedding(text):
    client = genai.Client(api_key=gemini_key)
    try:
        available = [m.name for m in client.models.list() if "embed" in m.name.lower()]
    except Exception:
        available = []
    candidates = available + EMBED_MODELS
    for model in candidates:
        try:
            result = client.models.embed_content(model=model, contents=text)
            return result.embeddings[0].values
        except Exception:
            continue
    raise Exception("No embedding model available. Check your Gemini API key.")

def get_endee_client():
    client = Endee(endee_token if endee_token else "")
    client.set_base_url(f"{endee_url.rstrip('/')}/api/v1")
    return client

def ingest_knowledge_base():
    hdrs = {"Content-Type": "application/json"}
    if endee_token:
        hdrs["Authorization"] = endee_token
    list_r = requests.get(f"{endee_url.rstrip('/')}/api/v1/index/list", headers=hdrs)
    existing = []
    if list_r.ok:
        data = list_r.json()
        if isinstance(data, list):
            existing = [i.get("name") for i in data]
        elif isinstance(data, dict):
            existing = [i.get("name") for i in data.get("indexes", [])]
    try:
        sample = f"{PLACEMENT_KB[0]['question']}\n{PLACEMENT_KB[0]['answer']}"
        embedding_dim = len(get_embedding(sample))
    except Exception as e:
        raise Exception(f"Failed to get embedding: {e}")
    if INDEX_NAME not in existing:
        cr = requests.post(f"{endee_url.rstrip('/')}/api/v1/index/create",
            json={"name": INDEX_NAME, "dimension": embedding_dim, "space_type": "cosine", "precision": "float16"}, headers=hdrs)
        if not cr.ok:
            raise Exception(f"Index creation failed: {cr.text}")
    client = get_endee_client()
    index  = client.get_index(name=INDEX_NAME)
    vectors = []
    progress = st.progress(0, text="Embedding knowledge base...")
    for i, item in enumerate(PLACEMENT_KB):
        embedding = get_embedding(f"{item['question']}\n{item['answer']}")
        vectors.append({"id": item["id"], "vector": embedding, "meta": {"topic": item["topic"], "question": item["question"], "answer": item["answer"]}})
        progress.progress((i + 1) / len(PLACEMENT_KB), text=f"Embedding {i+1}/{len(PLACEMENT_KB)}...")
    index.upsert(vectors)
    progress.empty()

def rag_query(question, topic_filter, top_k):
    client    = get_endee_client()
    index     = client.get_index(name=INDEX_NAME)
    query_vec = get_embedding(question)
    results   = index.query(vector=query_vec, top_k=top_k)
    if topic_filter != "All Topics":
        filtered = [r for r in results if r.get("meta", {}).get("topic") == topic_filter]
        if filtered:
            results = filtered
    context_parts = []
    sources = []
    for r in results[:top_k]:
        meta = r.get("meta", {})
        context_parts.append(f"Q: {meta.get('question','')}\nA: {meta.get('answer','')}")
        sources.append({"topic": meta.get("topic",""), "question": meta.get("question",""), "score": round(r.get("similarity", 0), 3)})
    context  = "\n\n---\n\n".join(context_parts)
    prompt   = f"You are an expert placement preparation coach. Use the retrieved knowledge to answer the student's question.\n\nRetrieved Context:\n{context}\n\nStudent Question: {question}\n\nProvide a clear structured answer with bullet points where helpful."
    ai = genai.Client(api_key=gemini_key)
    try:
        available = [m.name for m in ai.models.list()]
    except Exception:
        available = []
    gen_model = "gemini-1.5-flash"
    for pref in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.5"]:
        for m in available:
            if pref in m and "embed" not in m:
                gen_model = m
                break
    response = ai.models.generate_content(model=gen_model, contents=prompt)
    return response.text, sources

# ─── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎯 Placement Prep AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your intelligent interview companion - powered by Endee Vector DB + Google Gemini</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
endee_ok = gemini_ok = kb_ready = False

with col1:
    if gemini_key:
        st.markdown('<span class="status-ok">✅ Gemini Connected</span>', unsafe_allow_html=True)
        gemini_ok = True
    else:
        st.markdown('<span class="status-err">⚠️ Gemini key missing</span>', unsafe_allow_html=True)

with col2:
    if endee_url:
        try:
            get_endee_client().list_indexes()
            st.markdown('<span class="status-ok">✅ Endee Connected</span>', unsafe_allow_html=True)
            endee_ok = True
        except Exception as err:
            # show the exception text to help debugging
            st.markdown(f'<span class="status-err">❌ Endee: check server ({err})</span>', unsafe_allow_html=True)
            # optional debug output for environment variables
            st.text_area("🔍 Debug info", f"ENDEE_URL={endee_url}\nENDEE_AUTH_TOKEN={'<set>' if endee_token else '<empty>'}", height=80)
    else:
        st.markdown('<span class="status-err">⚠️ Endee URL missing</span>', unsafe_allow_html=True)

with col3:
    if endee_ok:
        try:
            get_endee_client().get_index(name=INDEX_NAME)
            st.markdown('<span class="status-ok">✅ Knowledge Base Ready</span>', unsafe_allow_html=True)
            kb_ready = True
        except Exception:
            st.markdown('<span class="status-err">⚠️ KB not ingested yet</span>', unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "📥 Load Knowledge Base", "📊 Browse Topics"])

with tab1:
    st.markdown("### Ask anything about placement preparation")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.markdown("**Quick questions:**")
    qcols    = st.columns(3)
    quick_qs = ["What is dynamic programming?", "How to design a URL shortener?", "Tell me about SOLID principles", "What is CAP theorem?", "How to answer Tell me about yourself?", "Explain TCP vs UDP"]
    for i, q in enumerate(quick_qs):
        if qcols[i % 3].button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state.pending_question = q
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user"><strong>🧑‍💻 You:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai"><strong>🤖 AI Coach:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            if show_sources and msg.get("sources"):
                for s in msg["sources"]:
                    st.markdown(f'<span class="source-chip">📌 {s["topic"]} | Score: {s["score"]}</span>', unsafe_allow_html=True)
    question = st.chat_input("Ask your placement question...")
    if hasattr(st.session_state, "pending_question"):
        question = st.session_state.pending_question
        del st.session_state.pending_question
    if question:
        if not gemini_ok or not endee_ok:
            st.error("Please configure Gemini API key and ensure Endee server is running.")
        elif not kb_ready:
            st.error("Knowledge base not loaded. Go to Load Knowledge Base tab first.")
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Retrieving knowledge and generating answer..."):
                try:
                    answer, sources = rag_query(question, selected_topic, top_k)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

with tab2:
    st.markdown("### 📥 Load Knowledge Base into Endee")
    st.info(f"This will embed {len(PLACEMENT_KB)} Q&A pairs across {len(topics)-1} topics into Endee using Gemini embeddings.")
    topic_counts = {}
    for item in PLACEMENT_KB:
        topic_counts[item["topic"]] = topic_counts.get(item["topic"], 0) + 1
    for t, c in topic_counts.items():
        st.markdown(f"- {t}: **{c} Q&As**")
    if st.button("🚀 Ingest Knowledge Base", type="primary", use_container_width=True):
        if not gemini_ok or not endee_ok:
            st.error("Configure Gemini API key and Endee server first.")
        else:
            try:
                ingest_knowledge_base()
                st.success(f"✅ Successfully ingested {len(PLACEMENT_KB)} Q&A pairs into Endee!")
                st.balloons()
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

with tab3:
    st.markdown("### 📊 Browse Knowledge Base by Topic")
    browse_topic = st.selectbox("Select topic", topics[1:], key="browse_sel")
    filtered     = [item for item in PLACEMENT_KB if item["topic"] == browse_topic]
    st.markdown(f"**{len(filtered)} questions in {browse_topic}**")
    for item in filtered:
        with st.expander(f"❓ {item['question']}"):
            st.markdown(item["answer"])
const { useState } = React;

function App() {
  const [projectPath, setProjectPath] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectId, setProjectId] = useState("");
  const [browseOpen, setBrowseOpen] = useState(false);
  const [browsePath, setBrowsePath] = useState("");
  const [browseParent, setBrowseParent] = useState(null);
  const [browseDirs, setBrowseDirs] = useState([]);
  const [browseBusy, setBrowseBusy] = useState(false);
  const [browseError, setBrowseError] = useState("");
  const [question, setQuestion] = useState("What is the architecture of this code?");
  const [topK, setTopK] = useState(5);
  const [maxContextChars, setMaxContextChars] = useState(2000);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState([]);
  const [status, setStatus] = useState({ type: "warn", text: "Idle" });
  const [busy, setBusy] = useState(false);

  const hasProjectPath = projectPath.trim().length > 0;
  const hasProjectId = projectId.trim().length > 0;
  const hasAnswer = answer.trim().length > 0;

  async function api(url, method = "GET", body = null) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }

  async function registerProject() {
    setBusy(true);
    setStatus({ type: "warn", text: "Registering project..." });
    try {
      const data = await api("/projects/register", "POST", {
        project_path: projectPath,
        name: projectName || null,
      });
      setProjectId(data.project_id);
      setStatus({ type: "ok", text: `Registered: ${data.project_id}` });
    } catch (e) {
      setStatus({ type: "err", text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function indexProject() {
    if (!projectId) return setStatus({ type: "err", text: "Project ID is required." });
    setBusy(true);
    setStatus({ type: "warn", text: "Indexing project..." });
    try {
      const data = await api(`/projects/${projectId}/index`, "POST");
      setStatus({ type: "ok", text: `Indexed ${data.chunks_indexed} chunks from ${data.scanned_files} files.` });
    } catch (e) {
      setStatus({ type: "err", text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function askQuestion() {
    if (!projectId) return setStatus({ type: "err", text: "Project ID is required." });
    setBusy(true);
    setStatus({ type: "warn", text: "Asking question..." });
    setAnswer("");
    setCitations([]);
    try {
      const data = await api(`/projects/${projectId}/ask`, "POST", {
        question,
        top_k: Number(topK),
        max_context_chars: Number(maxContextChars),
      });
      setAnswer(data.answer || "No answer returned.");
      setCitations(data.citations || []);
      setStatus({ type: "ok", text: "Answer received." });
    } catch (e) {
      setStatus({ type: "err", text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function loadDirectories(path = null) {
    setBrowseBusy(true);
    setBrowseError("");
    try {
      const query = path ? `?path=${encodeURIComponent(path)}` : "";
      const data = await api(`/filesystem/dirs${query}`);
      setBrowsePath(data.path || "");
      setBrowseParent(data.parent || null);
      setBrowseDirs(data.directories || []);
    } catch (e) {
      setBrowseError(e.message || "Unable to load directories.");
    } finally {
      setBrowseBusy(false);
    }
  }

  async function openBrowser() {
    setBrowseOpen(true);
    const seedPath = projectPath.trim() || null;
    await loadDirectories(seedPath);
  }

  function useBrowsedPath() {
    if (!browsePath) return;
    setProjectPath(browsePath);
    setBrowseOpen(false);
  }

  return (
    <div className="app-shell">
      <div className="app">
        <header className="hero">
          <div className="hero-copy">
            <div className="eyebrow">Engineering Workspace</div>
            <h1 className="title">Codebase Aware Assistant</h1>
            <p className="subtitle">
              Register repositories, build retrieval context, and ask grounded questions from one focused control
              surface.
            </p>
            <div className="hero-actions">
              <span className={`badge ${status.type}`}>{status.text}</span>
              <span className="hero-note">{busy ? "Processing request" : "Ready for the next operation"}</span>
            </div>
          </div>

          <div className="hero-stats">
            <article className="stat-card">
              <span className="stat-label">Project Path</span>
              <strong className="stat-value">{hasProjectPath ? "Connected" : "Not set"}</strong>
              <span className="stat-meta">{hasProjectPath ? projectPath : "Choose the repository root to begin."}</span>
            </article>
            <article className="stat-card">
              <span className="stat-label">Project ID</span>
              <strong className="stat-value">{hasProjectId ? "Registered" : "Pending"}</strong>
              <span className="stat-meta">{hasProjectId ? projectId : "Register a project to generate an ID."}</span>
            </article>
            <article className="stat-card stat-card-accent">
              <span className="stat-label">Answer State</span>
              <strong className="stat-value">{hasAnswer ? "Response Ready" : "Awaiting Query"}</strong>
              <span className="stat-meta">
                {hasAnswer ? `${citations.length} citation${citations.length === 1 ? "" : "s"} attached.` : "Ask a question to populate the analysis panel."}
              </span>
            </article>
          </div>
        </header>

        <main className="workspace">
          <section className="panel panel-setup stack">
            <div className="section-heading">
              <div>
                <div className="eyebrow">Setup</div>
                <h2>Project Configuration</h2>
              </div>
              <p>Select the repository root, optionally name it, then register and index the project.</p>
            </div>

            <div className="grid">
              <div className="field-group field-group-wide">
                <label>Project Path</label>
                <div className="input-with-action">
                  <input
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    placeholder="D:\\Projects\\my-repo"
                  />
                  <button type="button" className="button-secondary" onClick={openBrowser} disabled={busy}>
                    Browse
                  </button>
                </div>
              </div>

              <div className="field-group">
                <label>Project Name</label>
                <input
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My Project"
                />
              </div>
            </div>

            <div className="action-strip">
              <button onClick={registerProject} disabled={busy || !hasProjectPath}>
                Register Project
              </button>

              <div className="id-wrap field-group">
                <label>Project ID</label>
                <input value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="UUID" />
              </div>

              <button className="button-secondary" onClick={indexProject} disabled={busy || !hasProjectId}>
                Index Codebase
              </button>
            </div>
          </section>

          <section className="panel panel-query stack">
            <div className="section-heading">
              <div>
                <div className="eyebrow">Query</div>
                <h2>Assistant Prompting</h2>
              </div>
              <p>Refine retrieval depth and context size, then inspect the generated answer and evidence.</p>
            </div>

            <div className="field-group">
              <label>Question</label>
              <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
            </div>

            <div className="query-toolbar">
              <div className="compact-grid">
                <div className="field-group">
                  <label>Top K</label>
                  <input type="number" min="1" max="8" value={topK} onChange={(e) => setTopK(e.target.value)} />
                </div>
                <div className="field-group">
                  <label>Max Context Chars</label>
                  <input
                    type="number"
                    min="500"
                    max="30000"
                    value={maxContextChars}
                    onChange={(e) => setMaxContextChars(e.target.value)}
                  />
                </div>
              </div>

              <button onClick={askQuestion} disabled={busy || !hasProjectId || !question.trim()}>
                Run Analysis
              </button>
            </div>

            <section className="response-panel">
              <div className="response-heading">
                <h3>Response</h3>
                <span className="response-meta">{hasAnswer ? "Latest answer" : "No answer yet"}</span>
              </div>

              {hasAnswer ? (
                <div className="answer">{answer}</div>
              ) : (
                <div className="empty-state">
                  Register and index a project, then ask a question to see grounded results here.
                </div>
              )}

              {citations.length > 0 && (
                <div className="citations">
                  {citations.map((c, i) => (
                    <div className="citation" key={i}>
                      <div className="citation-file">
                        <code>{c.file}</code>
                      </div>
                      <div>Lines {c.start_line} - {c.end_line}</div>
                      <div>Score {Number(c.score).toFixed(4)}</div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </section>
        </main>
      </div>

      {browseOpen && (
        <div className="browser-overlay">
          <section className="browser-modal">
            <div className="browser-header">
              <div>
                <div className="eyebrow">Folder Browser</div>
                <h3>Choose Project Folder</h3>
              </div>
              <button type="button" className="button-ghost" onClick={() => setBrowseOpen(false)}>
                Close
              </button>
            </div>

            <div className="browser-path">{browsePath || "Loading..."}</div>

            <div className="browser-actions">
              <button
                type="button"
                className="button-secondary"
                onClick={() => browseParent && loadDirectories(browseParent)}
                disabled={browseBusy || !browseParent}
              >
                Up One Level
              </button>
              <button type="button" onClick={useBrowsedPath} disabled={!browsePath}>
                Use This Folder
              </button>
            </div>

            {browseError && <div className="browser-error">{browseError}</div>}

            <div className="browser-list">
              {browseDirs.map((dir) => (
                <button
                  key={dir.path}
                  type="button"
                  className="browser-item"
                  onClick={() => loadDirectories(dir.path)}
                  disabled={browseBusy}
                >
                  <span>{dir.name}</span>
                  <span className="browser-item-meta">Open</span>
                </button>
              ))}
              {!browseBusy && browseDirs.length === 0 && <div className="browser-empty">No subfolders found.</div>}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

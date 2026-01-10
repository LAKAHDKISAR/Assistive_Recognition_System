function CommandPanel({ onCommand, isConnected, currentMode }) {
  return (
    <div className="command-panel">
      <h3>Commands</h3>
      <div className="command-grid">
        <button
          className={`command-btn scan-btn ${
            currentMode === "SCAN" ? "active" : ""
          }`}
          onClick={() => onCommand("SCAN")}
          disabled={!isConnected}
          title="Switch to scan mode - detect and announce objects"
        >
          <span className="btn-icon">🔍</span>
          <span className="btn-text">Scan</span>
          <span className="btn-desc">Detect objects</span>
        </button>

        <button
          className={`command-btn guide-btn ${
            currentMode === "GUIDE" ? "active" : ""
          }`}
          onClick={() => onCommand("GUIDE")}
          disabled={!isConnected}
          title="Switch to guide mode - position guidance for selected object"
        >
          <span className="btn-icon">🎯</span>
          <span className="btn-text">Guide</span>
          <span className="btn-desc">Position help</span>
        </button>

        <button
          className="command-btn select-btn"
          onClick={() => onCommand("SELECT")}
          disabled={!isConnected}
          title="Select the largest detected object"
        >
          <span className="btn-icon">👆</span>
          <span className="btn-text">Select</span>
          <span className="btn-desc">Choose object</span>
        </button>

        <button
          className="command-btn read-btn"
          onClick={() => onCommand("READ")}
          disabled={!isConnected}
          title="Read text from selected object using OCR"
        >
          <span className="btn-icon">📖</span>
          <span className="btn-text">Read</span>
          <span className="btn-desc">OCR text</span>
        </button>
      </div>

      <div className="command-help">
        <h4>How to use:</h4>
        <ul>
          <li>
            <strong>Scan:</strong> Automatically detect and announce objects
          </li>
          <li>
            <strong>Guide:</strong> Get positioning feedback for closer
            inspection
          </li>
          <li>
            <strong>Select:</strong> Choose the largest object in view
          </li>
          <li>
            <strong>Read:</strong> Extract and read text from selected object
          </li>
        </ul>
      </div>
    </div>
  );
}

export default CommandPanel;

import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [backendMessage, setBackendMessage] = useState("Checking backend...");
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }

        return response.json();
      })
      .then((data) => {
        setBackendMessage(data.message);
      })
      .catch((requestError) => {
        setError(requestError.message);
      });
  }, []);

  return (
    <main>
      <h1>OpenAccessPaperScrapper</h1>
      <p>React frontend is running.</p>

      {error ? (
        <p>Backend error: {error}</p>
      ) : (
        <p>Backend response: {backendMessage}</p>
      )}
    </main>
  );
}

export default App;

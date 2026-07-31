import { useEffect, useState } from "react";

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setHealth(data);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">
        Frontend → Backend Test
      </h1>

      {health && (
        <pre className="bg-gray-100 p-4 rounded">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}

      {error && (
        <p className="text-red-600">
          Error: {error}
        </p>
      )}
    </div>
  );
}

export default App;
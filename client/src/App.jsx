import { useState } from "react";

const Spinner = () => (
  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
);

function App() {
  const [topic, setTopic] = useState("");
  const [generatedTweet, setGeneratedTweet] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerateTweet = async () => {
    if (!topic.trim()) {
      setError("Please enter a topic.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setGeneratedTweet("");

    try {
      const response = await fetch("http://127.0.0.1:5000/api/generate-tweet", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setGeneratedTweet(data.tweet);
    } catch (e) {
      console.error("Failed to fetch:", e);
      setError("Failed to generate tweet. Is the backend server running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex justify-center items-center font-sans">
      <div className="w-full max-w-2xl mx-auto p-8 space-y-8">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
            AI Tweet Generator
          </h1>
          <p className="mt-4 text-lg text-slate-400">
            Powered by Python, React, and{" "}
            <span className="font-semibold text-slate-300">Langfuse</span> for
            Observability.
          </p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-2xl shadow-slate-950/50">
          <div className="flex flex-col space-y-4">
            <label
              htmlFor="topic"
              className="text-md font-semibold text-slate-300"
            >
              What topic should the tweet be about?
            </label>
            <textarea
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., The future of renewable energy"
              className="w-full h-24 p-3 bg-slate-900/50 border border-slate-600 rounded-md focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition duration-200 resize-none"
              disabled={isLoading}
            />
            <button
              onClick={handleGenerateTweet}
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-3 px-4 rounded-md transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? <Spinner /> : "✨ Generate Tweet"}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 text-center p-4 rounded-lg">
            <p>{error}</p>
          </div>
        )}

        {generatedTweet && (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg animate-fade-in">
            <h3 className="text-lg font-semibold text-slate-300 mb-3">
              Generated Tweet:
            </h3>
            <p className="text-slate-200 whitespace-pre-wrap font-serif text-lg leading-relaxed">
              {generatedTweet}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

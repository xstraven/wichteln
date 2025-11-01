import { FormEvent, useState } from "react";
import { ApiError, revealMatch, RevealResponse } from "../api/client";

const Reveal = () => {
  const [identifier, setIdentifier] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RevealResponse | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!identifier.trim() || !name.trim()) {
      setError("Please enter both the group identifier and your name.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await revealMatch(identifier.trim(), name.trim());
      setResult(response);
    } catch (maybeApiError) {
      if (maybeApiError instanceof ApiError) {
        setError(maybeApiError.message);
      } else if (maybeApiError instanceof Error) {
        setError(maybeApiError.message);
      } else {
        setError("The snowglobe is a bit foggy. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setIdentifier("");
    setName("");
    setError(null);
    setResult(null);
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h1>Reveal Your Match</h1>
        <p>Enter the magical identifier and your name to uncover who you&apos;re gifting.</p>
      </div>

      <form className="panel-form" onSubmit={handleSubmit}>
        <label className="form-field">
          <span className="form-label">Group Identifier</span>
          <input
            type="text"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            placeholder="CozyPineMittens"
            autoComplete="off"
          />
        </label>

        <label className="form-field">
          <span className="form-label">Your name</span>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Taylor"
            autoComplete="off"
          />
        </label>

        {error ? <div className="alert error">{error}</div> : null}
        {result ? (
          <div className="alert success">
            <h2>Shh! 🎁</h2>
            <p>
              {result.participantName}, you&apos;re secretly shopping for{" "}
              <strong>{result.recipientName}</strong>.
            </p>
          </div>
        ) : null}

        <div className="form-actions">
          <button type="submit" className="cta primary" disabled={isLoading}>
            {isLoading ? "Checking the list..." : "Reveal"}
          </button>
          <button type="button" className="cta secondary" onClick={reset} disabled={isLoading}>
            Clear
          </button>
        </div>
      </form>
    </section>
  );
};

export default Reveal;

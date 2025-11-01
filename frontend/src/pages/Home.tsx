import { Link } from "react-router-dom";

const Home = () => (
  <section className="hero">
    <div className="hero-card">
      <h1>Spread Cheer, Secretly 🎁</h1>
      <p>
        Gather your favorite people, pick a whimsical three-word identifier, and let the elves
        handle the matching. No spreadsheets, no spoilers—just festive surprises.
      </p>

      <div className="cta-group">
        <Link to="/create" className="cta primary">
          Create a Group
        </Link>
        <Link to="/reveal" className="cta secondary">
          Reveal My Match
        </Link>
      </div>
    </div>

    <div className="feature-grid">
      <article className="feature-card">
        <h2>✨ Sparkly Simple</h2>
        <p>Input names, add gentle constraints (no gifting your partner!), and share a fun identifier.</p>
      </article>
      <article className="feature-card">
        <h2>🧝 Fair Elves</h2>
        <p>Our matching keeps everyone in the spirit—no self matches, no forbidden pairs, all smiles.</p>
      </article>
      <article className="feature-card">
        <h2>📬 Secret Reveal</h2>
        <p>Participants use the shared identifier and their name to discover who to surprise.</p>
      </article>
    </div>
  </section>
);

export default Home;

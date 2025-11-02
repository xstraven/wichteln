import { FormEvent, useMemo, useState } from "react";
import {
  ApiError,
  createGroup,
  CreateGroupPayload,
  GroupCreateResponse,
  IllegalPairPayload,
} from "../api/client";

const WORD_BANK = {
  first: [
    "Santa", "Elf", "Reindeer", "Rudolph", "Dasher", "Dancer", "Prancer", "Vixen", "Comet", "Cupid",
    "Donner", "Blitzen", "Snowman", "Gingerbread", "Nutcracker", "Angel", "Cherub", "Caroler", "Krampus", "Scrooge",
    "Frosty", "Jolly", "Merry", "Cheerful", "Magical", "Festive", "Sparkly", "Twinkling", "Shimmering", "Glowing",
    "Bright", "Radiant", "Gleaming", "Dazzling", "Luminous", "Enchanted", "Whimsical", "Joyful", "Jolting", "Singing",
    "Dancing", "Prancing", "Leaping", "Galloping", "Trotting", "Hopping", "Skipping", "Waltzing", "Spinning", "Twirling",
  ],
  second: [
    "Cinnamon", "Nutmeg", "Clementine", "Peppermint", "Gingerbread", "Candy", "Caramel", "Chocolate", "Vanilla", "Eggnog",
    "Cranberry", "Orange", "Lemon", "Honey", "Molasses", "Allspice", "Cardamom", "Anise", "Clove", "Ginger",
    "Hazelnut", "Almond", "Walnut", "Pine", "Cedar", "Fir", "Spruce", "Holly", "Mistletoe", "Frankincense",
    "Myrrh", "Rose", "Licorice", "Butterscotch", "Toffee", "Fudge", "Praline", "Nougat", "Truffle", "Ganache",
    "Frosting", "Icing", "Fondant", "Glaze", "Sugar", "Spice", "Mace", "Sage", "Coriander", "Cumin",
  ],
  third: [
    "Ornament", "Tinsel", "Garland", "Wreath", "Lights", "Candle", "Lantern", "Star", "Snowflake", "Icicle",
    "Stocking", "Ribbon", "Bow", "Gift", "Present", "Package", "Bell", "Chime", "Carol", "Song",
    "Hymn", "Choir", "Feast", "Dinner", "Supper", "Cake", "Cookie", "Pie", "Pudding", "Custard",
    "Compote", "Sauce", "Treat", "Sweet", "Dessert", "Beverage", "Punch", "Cocoa", "Coffee", "Tea",
    "Wassail", "Mulled", "Spiced", "Roasted", "Baked", "Glazed", "Tree", "Angel", "Sleigh", "Mittens",
  ],
};

const PASCAL_THREE_WORDS = /^[A-Z][a-z]+(?:[A-Z][a-z]+){2,}$/;

const randomIdentifier = () => {
  const first = WORD_BANK.first[Math.floor(Math.random() * WORD_BANK.first.length)];
  const second = WORD_BANK.second[Math.floor(Math.random() * WORD_BANK.second.length)];
  const third = WORD_BANK.third[Math.floor(Math.random() * WORD_BANK.third.length)];
  return `${first}${second}${third}`;
};

type ParsedNames = {
  names: string[];
  duplicates: string[];
};

const parseNames = (raw: string): ParsedNames => {
  const tokens = raw
    .split(/\r?\n|,/)
    .map((token) => token.trim())
    .filter(Boolean);

  const seen = new Map<string, string>();
  const duplicates = new Set<string>();
  const unique: string[] = [];

  tokens.forEach((name) => {
    const key = name.toLowerCase();
    if (!seen.has(key)) {
      seen.set(key, name);
      unique.push(name);
    } else {
      duplicates.add(name);
    }
  });

  return { names: unique, duplicates: Array.from(duplicates) };
};

const CreateGroup = () => {
  const [identifier, setIdentifier] = useState<string>(randomIdentifier());
  const [description, setDescription] = useState<string>("");
  const [namesInput, setNamesInput] = useState<string>("");
  const [illegalPairs, setIllegalPairs] = useState<IllegalPairPayload[]>([]);
  const [newPair, setNewPair] = useState<IllegalPairPayload>({ giver: "", receiver: "" });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<GroupCreateResponse | null>(null);

  const { names, duplicates } = useMemo(() => parseNames(namesInput), [namesInput]);

  const identifierError = useMemo(() => {
    if (!identifier.trim()) {
      return "Choose a festive three-word identifier (e.g. GingerbreadStarGazer).";
    }
    if (!PASCAL_THREE_WORDS.test(identifier.trim())) {
      return "Identifier should be PascalCase and at least three words (e.g. CozyPineMittens).";
    }
    return null;
  }, [identifier]);

  const canSubmit = identifierError === null && names.length >= 2;

  const handleAddPair = () => {
    if (!newPair.giver || !newPair.receiver || newPair.giver === newPair.receiver) {
      return;
    }
    const exists = illegalPairs.some(
      (pair) => pair.giver === newPair.giver && pair.receiver === newPair.receiver,
    );
    if (exists) {
      return;
    }
    setIllegalPairs((prev) => [...prev, newPair]);
    setNewPair({ giver: "", receiver: "" });
  };

  const handleRemovePair = (index: number) => {
    setIllegalPairs((prev) => prev.filter((_, idx) => idx !== index));
  };

  const resetForm = () => {
    setIdentifier(randomIdentifier());
    setDescription("");
    setNamesInput("");
    setIllegalPairs([]);
    setNewPair({ giver: "", receiver: "" });
    setError(null);
    setSuccess(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!canSubmit) {
      setError("Please add at least two names and provide a valid identifier.");
      return;
    }

    const filteredPairs = illegalPairs.filter(
      (pair) => names.includes(pair.giver) && names.includes(pair.receiver),
    );
    if (filteredPairs.length !== illegalPairs.length) {
      setIllegalPairs(filteredPairs);
    }

    const payload: CreateGroupPayload = {
      identifier: identifier.trim(),
      description: description.trim() || undefined,
      participants: names.map((name) => ({ name })),
      illegalPairs: filteredPairs,
    };

    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await createGroup(payload);
      setSuccess(response);
    } catch (maybeApiError) {
      if (maybeApiError instanceof ApiError) {
        setError(maybeApiError.message);
      } else if (maybeApiError instanceof Error) {
        setError(maybeApiError.message);
      } else {
        setError("An unexpected blizzard hit the server. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="panel festive-panel">
      <div className="panel-header">
        <div className="festive-header">
          <h1>Create a Secret Santa Group</h1>
        </div>
        <p>
          Add your participant list, sprinkle in any forbidden combos, and share the identifier with
          your festive crew.
        </p>
      </div>

      <form className="panel-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">
              Identifier <span className="badge">Three words</span>
            </span>
            <div className="identifier-input">
              <input
                type="text"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                placeholder="CozyPineMittens"
                aria-invalid={identifierError ? "true" : "false"}
              />
              <button
                type="button"
                className="ghost-button"
                onClick={() => setIdentifier(randomIdentifier())}
                title="Generate a fresh suggestion"
              >
                Shuffle ✨
              </button>
            </div>
            {identifierError ? <small className="form-hint error">{identifierError}</small> : null}
          </label>

          <label className="form-field">
            <span className="form-label">Optional notes</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="e.g. Budget 25€, reveal gifts at the December brunch."
              rows={3}
            />
          </label>
        </div>

        <label className="form-field">
          <span className="form-label">Participants</span>
          <textarea
            value={namesInput}
            onChange={(event) => setNamesInput(event.target.value)}
            placeholder="Add one name per line or separate with commas"
            rows={6}
          />
          <small className="form-hint">
            {names.length === 0
              ? "You need at least two merry participants."
              : `${names.length} participant${names.length === 1 ? "" : "s"} detected.`}
          </small>
          {duplicates.length > 0 ? (
            <small className="form-hint warning">
              Duplicates removed: {duplicates.join(", ")}.
            </small>
          ) : null}
        </label>

        {names.length >= 2 ? (
          <div className="pill-tray" aria-live="polite">
            {names.map((name) => (
              <span key={name} className="pill">
                {name}
              </span>
            ))}
          </div>
        ) : null}

        <fieldset className="form-field">
          <legend className="form-label">Forbidden pairings</legend>
          <p className="form-hint">
            Make sure certain elves don&apos;t gift each other (like partners or roommates).
          </p>

          <div className="pair-input-row">
            <select
              value={newPair.giver}
              onChange={(event) => setNewPair((prev) => ({ ...prev, giver: event.target.value }))}
            >
              <option value="">Select giver</option>
              {names.map((name) => (
                <option key={`giver-${name}`} value={name}>
                  {name}
                </option>
              ))}
            </select>

            <span className="pair-arrow" aria-hidden="true">
              ✨
            </span>

            <select
              value={newPair.receiver}
              onChange={(event) =>
                setNewPair((prev) => ({ ...prev, receiver: event.target.value }))
              }
            >
              <option value="">Select receiver</option>
              {names.map((name) => (
                <option key={`receiver-${name}`} value={name}>
                  {name}
                </option>
              ))}
            </select>

            <button type="button" className="ghost-button" onClick={handleAddPair}>
              Add
            </button>
          </div>

          {illegalPairs.length > 0 ? (
            <ul className="pair-list">
              {illegalPairs.map((pair, index) => (
                <li key={`${pair.giver}-${pair.receiver}`}>
                  <span>
                    {pair.giver} → {pair.receiver}
                  </span>
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => handleRemovePair(index)}
                    aria-label={`Remove forbidden pair ${pair.giver} to ${pair.receiver}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <small className="form-hint muted">No forbidden pairs added yet.</small>
          )}
        </fieldset>

        {error ? <div className="alert error">{error}</div> : null}
        {success ? (
          <div className="alert success">
            <h2>Group ready! ❄️</h2>
            <p>
              Share <strong>{success.identifier}</strong> with your group. We matched{" "}
              <strong>{success.participantCount}</strong>{" "}
              participant{success.participantCount === 1 ? "" : "s"} in secret.
            </p>
            {success.illegalPairCount > 0 ? (
              <p>
                Honored <strong>{success.illegalPairCount}</strong> forbidden pairing
                {success.illegalPairCount === 1 ? "" : "s"}.
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="form-actions">
          <button type="submit" className="cta primary" disabled={!canSubmit || isSubmitting}>
            {isSubmitting ? "Assembling elves..." : "Create group"}
          </button>
          <button type="button" className="cta secondary" onClick={resetForm} disabled={isSubmitting}>
            Reset
          </button>
        </div>
      </form>
    </section>
  );
};

export default CreateGroup;

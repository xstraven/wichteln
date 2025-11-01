from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from wichteln.database import get_db
from wichteln.models import Exchange, Participant, Match, Constraint
from wichteln.utils import generate_secret_santa_matches, generate_unique_code
from wichteln.email_service import email_service
import typing

router = APIRouter()

def base_template(title: str, content):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #d32f2f; text-align: center; margin-bottom: 30px; }}
            h2 {{ color: #333; border-bottom: 2px solid #d32f2f; padding-bottom: 10px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, textarea, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
            button {{ background-color: #d32f2f; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background-color: #b71c1c; }}
            .participants {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .participant {{ margin-bottom: 10px; padding: 10px; background: white; border-radius: 3px; }}
            .success {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
            .code {{ font-family: monospace; font-size: 18px; background: #fffde7; padding: 10px; border-radius: 5px; text-align: center; }}
            a {{ color: #d32f2f; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            {content}
        </div>
    </body>
    </html>
    """

@router.get("/", response_class=HTMLResponse)
async def home():
    content = """
        <h1>🎁 Secret Santa Exchange</h1>
        <p>Welcome to Wichteln! Create and manage your secret santa gift exchanges.</p>
        <div>
            <h2>Quick Start</h2>
            <p>1. Create a new exchange</p>
            <p>2. Add participants with their email addresses</p>
            <p>3. Set any constraints (who can't give to whom)</p>
            <p>4. Generate matches and send codes</p>
            <p>5. Participants use their codes to find out who they're buying for</p>
        </div>
        <div>
            <h2>Actions</h2>
            <a href="/create" style="margin-right: 20px;">Create New Exchange</a>
            <a href="/lookup">Look Up Your Recipient</a>
        </div>
    """
    return base_template("Secret Santa Exchange", content)

@router.get("/create", response_class=HTMLResponse)
async def create_exchange_form():
    content = """
        <h1>Create New Exchange</h1>
        <form method="post" action="/create">
            <div class="form-group">
                <label for="name">Exchange Name:</label>
                <input type="text" name="name" id="name" required placeholder="e.g. Office Secret Santa 2024">
            </div>
            <div class="form-group">
                <label for="description">Description (optional):</label>
                <textarea name="description" id="description" placeholder="Any additional details about the exchange..."></textarea>
            </div>
            <button type="submit">Create Exchange</button>
        </form>
    """
    return base_template("Create Exchange", content)

@router.post("/create", response_class=HTMLResponse)
async def create_exchange(
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    identifier = generate_unique_code(8)
    exchange = Exchange(name=name, identifier=identifier, description=description)
    db.add(exchange)
    await db.commit()
    await db.refresh(exchange)
    
    content = f"""
        <h1>Exchange Created!</h1>
        <p>Your exchange '{name}' has been created successfully.</p>
        <p>Share this identifier with participants: <span class="code">{exchange.identifier}</span></p>
        <a href="/exchange/{exchange.id}/participants">Add Participants</a>
        <br><br>
        <a href="/">Back to Home</a>
    """
    return base_template("Exchange Created", content)

@router.get("/exchange/{exchange_id}/participants", response_class=HTMLResponse)
async def add_participants_form(exchange_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exchange).where(Exchange.id == exchange_id))
    exchange = result.scalar_one_or_none()
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    content = f"""
        <h1>Add Participants to '{exchange.name}'</h1>
        <form method="post" action="/exchange/{exchange_id}/participants">
            <div class="form-group">
                <label for="participants">Participants (one per line, format: Name &lt;email@example.com&gt;):</label>
                <textarea name="participants" id="participants" required placeholder="Alice &lt;alice@example.com&gt;&#10;Bob &lt;bob@example.com&gt;&#10;Charlie &lt;charlie@example.com&gt;" style="height: 200px;"></textarea>
            </div>
            <button type="submit">Add Participants</button>
        </form>
        <a href="/">Back to Home</a>
    """
    return base_template("Add Participants", content)

@router.post("/exchange/{exchange_id}/participants", response_class=HTMLResponse)  
async def add_participants(
    exchange_id: int,
    participants: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Exchange).where(Exchange.id == exchange_id))
    exchange = result.scalar_one_or_none()
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    participant_list = []
    for line in participants.strip().split('\n'):
        line = line.strip()
        if '<' in line and '>' in line:
            name = line.split('<')[0].strip()
            email = line.split('<')[1].split('>')[0].strip()
        else:
            continue
            
        code = generate_unique_code()
        participant = Participant(
            name=name,
            email=email,
            code=code,
            exchange_id=exchange_id
        )
        participant_list.append(participant)
        db.add(participant)
    
    await db.commit()
    
    # Send codes via email
    await email_service.send_participant_codes(participant_list, exchange.name)
    
    participants_html = "\n".join([f'<div class="participant">{p.name} ({p.email}) - Code: {p.code}</div>' for p in participant_list])
    
    content = f"""
        <h1>Participants Added!</h1>
        <p>Added {len(participant_list)} participants to '{exchange.name}'.</p>
        <p>Unique codes have been sent to each participant's email address.</p>
        <div class="participants">
            <h2>Participants:</h2>
            {participants_html}
        </div>
        <a href="/exchange/{exchange_id}/generate">Generate Matches</a>
        <br><br>
        <a href="/">Back to Home</a>
    """
    return base_template("Participants Added", content)

@router.get("/exchange/{exchange_id}/generate", response_class=HTMLResponse)
async def generate_matches_page(exchange_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exchange).where(Exchange.id == exchange_id))
    exchange = result.scalar_one_or_none()
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    result = await db.execute(select(Participant).where(Participant.exchange_id == exchange_id))
    participants = result.scalars().all()
    
    if len(participants) < 2:
        content = f"""
            <h1>Error</h1>
            <p>You need at least 2 participants to generate matches.</p>
            <a href="/exchange/{exchange_id}/participants">Add More Participants</a>
            <br><br>
            <a href="/">Back to Home</a>
        """
        return base_template("Error", content)
    
    matches = generate_secret_santa_matches([p.id for p in participants])
    
    for giver_id, receiver_id in matches.items():
        match = Match(
            exchange_id=exchange_id,
            giver_id=giver_id,
            receiver_id=receiver_id
        )
        db.add(match)
    
    exchange.is_completed = True
    await db.commit()
    
    match_details = []
    for giver_id, receiver_id in matches.items():
        giver = next(p for p in participants if p.id == giver_id)
        receiver = next(p for p in participants if p.id == receiver_id)
        match_details.append((giver, receiver))
    
    matches_html = "\n".join([f'<div class="participant">{giver.name} ({giver.code}) → {receiver.name}</div>' for giver, receiver in match_details])
    
    content = f"""
        <h1>Matches Generated!</h1>
        <p>Secret Santa matches have been created for '{exchange.name}'.</p>
        <div class="participants">
            <h2>Generated Matches:</h2>
            {matches_html}
        </div>
        <p>Each participant should use their code to look up who they're buying for.</p>
        <a href="/lookup">Look Up Recipient</a>
        <br><br>
        <a href="/">Back to Home</a>
    """
    return base_template("Matches Generated", content)

@router.get("/lookup", response_class=HTMLResponse)
async def lookup_form():
    content = """
        <h1>Look Up Your Recipient</h1>
        <form method="post" action="/lookup">
            <div class="form-group">
                <label for="code">Enter your code:</label>
                <input type="text" name="code" id="code" required placeholder="e.g. ABCDE">
            </div>
            <button type="submit">Find My Recipient</button>
        </form>
        <a href="/">Back to Home</a>
    """
    return base_template("Look Up Recipient", content)

@router.post("/lookup", response_class=HTMLResponse)
async def lookup_recipient(code: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Participant).where(Participant.code == code.upper()))
    participant = result.scalar_one_or_none()
    
    if not participant:
        content = """
            <h1>Code Not Found</h1>
            <p>The code you entered was not found. Please check and try again.</p>
            <a href="/lookup">Try Again</a>
            <br><br>
            <a href="/">Back to Home</a>
        """
        return base_template("Code Not Found", content)
    
    result = await db.execute(select(Match).where(Match.giver_id == participant.id))
    match = result.scalar_one_or_none()
    
    if not match:
        content = """
            <h1>No Match Found</h1>
            <p>Matches haven't been generated yet for your exchange.</p>
            <a href="/">Back to Home</a>
        """
        return base_template("No Match Found", content)
    
    result = await db.execute(select(Participant).where(Participant.id == match.receiver_id))
    receiver = result.scalar_one_or_none()
    
    content = f"""
        <h1>🎁 Your Recipient</h1>
        <div style="font-size: 18px; margin-bottom: 20px;">Hello {participant.name}!</div>
        <div>
            <p>You are the Secret Santa for:</p>
            <div class="code">{receiver.name}</div>
            <p>Email: {receiver.email}</p>
        </div>
        <p>Happy gift giving! 🎄</p>
        <a href="/">Back to Home</a>
    """
    return base_template("Your Recipient", content)

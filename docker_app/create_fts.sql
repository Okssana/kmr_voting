-- Create FTS table for roll_call_voting_kmr table
-- This will enable full-text search across key text columns

CREATE VIRTUAL TABLE roll_call_voting_kmr_fts USING fts5(
    DPName_normalized,
    Faction,
    DPGolos,
    GL_Text,
    PD_NPP,
    RESULT,
    company,
    address,
    district,
    person,
    date_description,
    content='roll_call_voting_kmr',
    content_rowid='id'
);

-- Populate the FTS table with existing data
INSERT INTO roll_call_voting_kmr_fts(
    rowid, 
    DPName_normalized, 
    Faction, 
    DPGolos, 
    GL_Text, 
    PD_NPP, 
    RESULT, 
    company, 
    address, 
    district, 
    person, 
    date_description
)
SELECT 
    id,
    DPName_normalized, 
    Faction, 
    DPGolos, 
    GL_Text, 
    PD_NPP, 
    RESULT, 
    company, 
    address, 
    district, 
    person, 
    date_description
FROM roll_call_voting_kmr;

-- Create triggers to keep FTS table in sync with main table
CREATE TRIGGER roll_call_voting_kmr_ai AFTER INSERT ON roll_call_voting_kmr BEGIN
  INSERT INTO roll_call_voting_kmr_fts(
    rowid, DPName_normalized, Faction, DPGolos, GL_Text, PD_NPP, 
    RESULT, company, address, district, person, date_description
  )
  VALUES (
    new.id, new.DPName_normalized, new.Faction, new.DPGolos, new.GL_Text, new.PD_NPP,
    new.RESULT, new.company, new.address, new.district, new.person, new.date_description
  );
END;

CREATE TRIGGER roll_call_voting_kmr_ad AFTER DELETE ON roll_call_voting_kmr BEGIN
  INSERT INTO roll_call_voting_kmr_fts(roll_call_voting_kmr_fts, rowid, DPName_normalized, Faction, DPGolos, GL_Text, PD_NPP, RESULT, company, address, district, person, date_description)
  VALUES('delete', old.id, old.DPName_normalized, old.Faction, old.DPGolos, old.GL_Text, old.PD_NPP, old.RESULT, old.company, old.address, old.district, old.person, old.date_description);
END;

CREATE TRIGGER roll_call_voting_kmr_au AFTER UPDATE ON roll_call_voting_kmr BEGIN
  INSERT INTO roll_call_voting_kmr_fts(roll_call_voting_kmr_fts, rowid, DPName_normalized, Faction, DPGolos, GL_Text, PD_NPP, RESULT, company, address, district, person, date_description)
  VALUES('delete', old.id, old.DPName_normalized, old.Faction, old.DPGolos, old.GL_Text, old.PD_NPP, old.RESULT, old.company, old.address, old.district, old.person, old.date_description);
  INSERT INTO roll_call_voting_kmr_fts(
    rowid, DPName_normalized, Faction, DPGolos, GL_Text, PD_NPP, 
    RESULT, company, address, district, person, date_description
  )
  VALUES (
    new.id, new.DPName_normalized, new.Faction, new.DPGolos, new.GL_Text, new.PD_NPP,
    new.RESULT, new.company, new.address, new.district, new.person, new.date_description
  );
END;
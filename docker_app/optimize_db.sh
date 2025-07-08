#!/bin/bash
# This script optimizes the SQLite database for better performance

# Path to your database
DB_PATH="/opt/datasette/kmr_voting_data.db"

# Create a temporary file for SQL commands
TMP_SQL=$(mktemp)

# Write optimization SQL commands
cat > $TMP_SQL << 'SQL'
-- Add indexes for commonly queried columns
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_faction ON roll_call_voting_kmr(Faction);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_district ON roll_call_voting_kmr(district);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_result ON roll_call_voting_kmr(RESULT);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname ON roll_call_voting_kmr(DPName);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_faction ON roll_call_voting_kmr(DPGolos);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_district_faction ON roll_call_voting_kmr(DPName, district, Faction);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname ON roll_call_voting_kmr(DPName_normalized);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_district ON roll_call_voting_kmr(DPName_normalized, district);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_result ON roll_call_voting_kmr(DPName_normalized, RESULT);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_district_result ON roll_call_voting_kmr(DPName_normalized, district, RESULT);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_dpname_district_faction ON roll_call_voting_kmr(DPName_normalized, district, Faction);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_district_faction ON roll_call_voting_kmr(district, Faction);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_district_result ON roll_call_voting_kmr(district, RESULT);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_faction_result ON roll_call_voting_kmr(Faction, RESULT);
CREATE INDEX IF NOT EXISTS idx_roll_call_voting_kmr_faction_district ON roll_call_voting_kmr(Faction, DPGolos);

-- For the unique_votings table
CREATE INDEX IF NOT EXISTS idx_unique_votings_result ON unique_votings(RESULT);
CREATE INDEX IF NOT EXISTS idx_unique_votings_company ON unique_votings(company);
CREATE INDEX IF NOT EXISTS idx_unique_votings_district ON unique_votings(district);

-- Analyze the database to improve query planning
ANALYZE;

-- Vacuum the database to reclaim space and defragment
VACUUM;
SQL

# Execute the SQL commands
echo "Optimizing database..."
sqlite3 "$DB_PATH" < $TMP_SQL

# Remove the temporary file
rm $TMP_SQL

echo "Database optimization complete!"
echo "Important: Restart your Datasette container for changes to take effect."
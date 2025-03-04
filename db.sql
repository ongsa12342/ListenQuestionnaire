-- 1) Create the experiment database if it doesn't exist
CREATE DATABASE IF NOT EXISTS experiment;
USE experiment;

-- 2) Create the participants table
CREATE TABLE IF NOT EXISTS participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_name VARCHAR(255)
);

-- 3) Create the resources table
CREATE TABLE IF NOT EXISTS resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filenames VARCHAR(255),
    folder_paths VARCHAR(255),
    descriptions VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sequence_id INT NOT NULL,
    stimuli_id INT NOT NULL,
    trial INT NOT NULL,
    index_order INT NOT NULL,
    FOREIGN KEY (stimuli_id) REFERENCES resources(id)
);

-- 4) Create the sequence_info table matching df_final structure
--    df_final columns: [sequence_id, stimuli_id, trial, index_order]
-- Create a new table for sequence info (metadata)
CREATE TABLE IF NOT EXISTS sequence_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sequence_id INT NOT NULL,
    sequence_name VARCHAR(255) NULL,
    time_created DATETIME NOT NULL,
    folder_path VARCHAR(255) NOT NULL,
    choice_set_size INT NOT NULL,
    n_trials INT NOT NULL
);

-- 5) A view that joins sequence_info + resources
CREATE OR REPLACE VIEW sequence_view AS
SELECT
    si.id AS sequence_info_pk,
    si.sequence_id,
    si.sequence_name,
    si.time_created,
    si.folder_path,
    si.choice_set_size,
    si.n_trials,
    s.id AS sequences_pk,
    s.trial,
    s.index_order,
    s.stimuli_id,
    r.id AS resource_id,
    r.filenames AS resource_filenames,
    r.folder_paths AS resource_folder_paths,
    r.descriptions AS resource_descriptions
FROM sequence_info si
JOIN sequences s ON si.sequence_id = s.sequence_id
JOIN resources r ON s.stimuli_id = r.id;

CREATE TABLE IF NOT EXISTS trial_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,        -- references participants(id)
    sequence_id INT NOT NULL,           -- references sequence_info(sequence_id) or just an int
    trial_index INT NOT NULL,           -- which trial? (0, 1, 2, ...)
    best_stimulus INT NOT NULL,      -- references resources(id)
    worst_stimulus INT NOT NULL,     -- references resources(id)
    submitted_at DATETIME NOT NULL,     -- when did user press "Submit"?
    FOREIGN KEY (participant_id) REFERENCES participants(id),
    FOREIGN KEY (best_stimulus) REFERENCES resources(id),
    FOREIGN KEY (worst_stimulus) REFERENCES resources(id),
    FOREIGN KEY (sequence_id) REFERENCES sequence_info(sequence_id)
);

CREATE TABLE IF NOT EXISTS final_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,     -- references participants(id)
    sequence_id INT NOT NULL,        -- references sequence_info(sequence_id) or just an int
    resource_id INT NOT NULL,        -- references resources(id)
    final_score FLOAT NOT NULL,      -- the final "V" or strength
    rank_position INT NOT NULL,      -- if you want the final rank (1=best, 2=second, etc.)
    computed_at DATETIME NOT NULL,   -- when did you compute these final scores?

    FOREIGN KEY (participant_id) REFERENCES participants(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (sequence_id) REFERENCES sequence_info(sequence_id)
);

import sys
import os
import random
import pandas as pd
import datetime

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QRadioButton,
    QButtonGroup, QInputDialog
)

from database_utils import DBManager  # Your DB manager

ALPHA = 0.1  # Learning rate

class ExperimentWindow(QMainWindow):
    def __init__(self, sequence_id=1):
        super().__init__()
        self.setWindowTitle("Stimuli Selection Experiment (Using resource_id)")

        self.db_manager = DBManager()
        self.sequence_id = sequence_id

        # 1) Connect to DB and ask for participant name
        engine = self.db_manager.connect()
        participant_name, ok = QInputDialog.getText(self, "Participant Name", "Please enter your name:")
        if not ok or not participant_name.strip():
            QMessageBox.critical(self, "Error", "A participant name is required!")
            sys.exit(1)
        self.participant_name = participant_name.strip()
        self.participant_id = self.get_or_create_participant(self.participant_name)

        # 2) Read from 'sequence_view' and filter for sequence_id
        df_view = self.db_manager.read_table("sequence_view", engine)
        df_view = df_view[df_view["sequence_id"] == sequence_id].copy()
        if df_view.empty:
            QMessageBox.critical(self, "Error", f"No rows found in 'sequence_view' for sequence_id={sequence_id}")
            sys.exit(1)

        # 3) Build a dict to map resource_id -> audio_path
        #    So we can easily look up the file for each resource ID
        self.audio_map = {}
        for _, row in df_view.iterrows():
            res_id = row["resource_id"]
            folder_path = row["folder_path"]     # or row["resource_folder_paths"] if that's your column
            filename = row["resource_filenames"]
            full_path = os.path.join(folder_path, filename)
            self.audio_map[res_id] = full_path

        # 4) Sort by trial/index_order and group
        df_view.sort_values(["trial", "index_order"], inplace=True)
        df_view.reset_index(drop=True, inplace=True)

        # Build a list of trials: each trial is a list of resource IDs
        self.trials = []
        grouped = df_view.groupby("trial")
        for trial_id, group_df in grouped:
            group_df = group_df.sort_values("index_order")
            resource_ids_this_trial = list(group_df["resource_id"])
            self.trials.append(resource_ids_this_trial)

        # 5) Initialize self.V keyed by resource_id (one entry per unique resource)
        unique_res_ids = df_view["resource_id"].unique()
        self.V = {res_id: 0 for res_id in unique_res_ids}

        # 6) Trial counters, etc.
        self.current_trial_index = 0
        self.N_TRIALS = len(self.trials)
        print(self.trials)

        # 7) Set up UI
        self.player = QMediaPlayer()
        self.player.setVolume(100)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        intro_text = (
            f"Participant: {self.participant_name} (ID: {self.participant_id})\n"
            f"Sequence_id={sequence_id}. Select one Best and one Worst for each trial."
        )
        self.instruction_label = QLabel(intro_text)
        self.main_layout.addWidget(self.instruction_label)

        self.table_widget = QTableWidget()
        self.main_layout.addWidget(self.table_widget)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_choice)
        self.main_layout.addWidget(self.submit_button)

        self.update_display_for_trial()

    def __del__(self):
        self.db_manager.close()

    def get_or_create_participant(self, participant_name):
        """
        Look up a participant by name; if not found, insert a new row and return its id.
        """
        df_participants = self.db_manager.read_table("participants")
        existing = df_participants[df_participants["participant_name"] == participant_name]
        if not existing.empty:
            participant_id = int(existing.iloc[0]["id"])
        else:
            new_participant_df = pd.DataFrame([{"participant_name": participant_name}])
            self.db_manager.append_table("participants", new_participant_df)
            df_participants = self.db_manager.read_table("participants")
            new_entry = df_participants[df_participants["participant_name"] == participant_name]
            if new_entry.empty:
                raise Exception("Failed to add new participant.")
            participant_id = int(new_entry.iloc[0]["id"])
        return participant_id

    def update_display_for_trial(self):
        """
        Show the stimuli in the current trial as rows in the table.
        """
        self.player.stop()

        if self.current_trial_index >= self.N_TRIALS:
            self.show_final_results()
            return

        # resource_ids_for_this_trial is a list of resource IDs
        resource_ids_for_this_trial = self.trials[self.current_trial_index]

        self.table_widget.clear()
        self.table_widget.setRowCount(len(resource_ids_for_this_trial))
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Play", "Best", "Worst"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        self.best_button_group = QButtonGroup(self.table_widget)
        self.best_button_group.setExclusive(True)
        self.worst_button_group = QButtonGroup(self.table_widget)
        self.worst_button_group.setExclusive(True)

        for row_idx, res_id in enumerate(resource_ids_for_this_trial):
            # "Play" button
            play_button = QPushButton("Play")
            audio_path = self.audio_map[res_id]
            play_button.clicked.connect(lambda _, p=audio_path: self.play_sound(p))
            self.table_widget.setCellWidget(row_idx, 0, play_button)

            # Radio for "Best"
            rbtn_best = QRadioButton()
            self.table_widget.setCellWidget(row_idx, 1, rbtn_best)
            self.best_button_group.addButton(rbtn_best, row_idx)

            # Radio for "Worst"
            rbtn_worst = QRadioButton()
            self.table_widget.setCellWidget(row_idx, 2, rbtn_worst)
            self.worst_button_group.addButton(rbtn_worst, row_idx)

        self.table_widget.resizeColumnsToContents()

    def play_sound(self, path):
        url = QUrl.fromLocalFile(path)
        print(url)
        self.player.setMedia(QMediaContent(url))
        self.player.play()

    def submit_choice(self):
        if self.current_trial_index >= self.N_TRIALS:
            self.show_final_results()
            return

        # Get the resource IDs for this trial
        resource_ids_for_this_trial = self.trials[self.current_trial_index]
        best_row = self.best_button_group.checkedId()
        worst_row = self.worst_button_group.checkedId()

        # Validate user input
        if best_row == -1 or worst_row == -1:
            QMessageBox.warning(self, "Invalid Selection", "Please select one Best and one Worst.")
            return
        if best_row == worst_row:
            QMessageBox.warning(self, "Invalid Selection", "Best and Worst cannot be the same row.")
            return

        # Map the chosen row -> resource_id
        best_res_id = resource_ids_for_this_trial[best_row]
        worst_res_id = resource_ids_for_this_trial[worst_row]

        # Update 'best'
        for other_res_id in resource_ids_for_this_trial:
            if other_res_id != best_res_id:
                error = 1 - (self.V[best_res_id] - self.V[other_res_id])
                self.V[best_res_id] += ALPHA * error

        # Update 'worst'
        for other_res_id in resource_ids_for_this_trial:
            if other_res_id != worst_res_id:
                error = 0 - (self.V[worst_res_id] - self.V[other_res_id])
                self.V[worst_res_id] += ALPHA * error

        # Insert into trial_results
        df_trial = pd.DataFrame([{
            "participant_id": self.participant_id,
            "sequence_id": self.sequence_id,
            "trial_index": self.current_trial_index,
            "best_stimulus": best_res_id,
            "worst_stimulus": worst_res_id,
            "submitted_at": datetime.datetime.now()
        }])
        self.db_manager.append_table("trial_results", df_trial)

        self.current_trial_index += 1
        self.update_display_for_trial()

    def show_final_results(self):
        self.player.stop()

        # Clear layout
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        final_label = QLabel("Final Ranking (Best to Worst):")
        self.main_layout.addWidget(final_label)

        # Sort self.V by descending strength
        sorted_stimuli = sorted(self.V.items(), key=lambda x: x[1], reverse=True)
        print(self.V)
        print(sorted_stimuli)
        # e.g. [(resource_id, final_score), ...]

        df_scores_list = []
        final_table = QTableWidget()
        final_table.setColumnCount(2)
        final_table.setRowCount(len(sorted_stimuli))
        final_table.setHorizontalHeaderLabels(["Rank", "Resource ID"])
        final_table.verticalHeader().setVisible(False)
        final_table.horizontalHeader().setStretchLastSection(True)

        rank_position = 1
        for (res_id, score) in sorted_stimuli:
            df_scores_list.append({
                "participant_id": self.participant_id,
                "sequence_id": self.sequence_id,
                "resource_id": res_id,
                "final_score": score,
                "rank_position": rank_position,
                "computed_at": datetime.datetime.now()
            })

            # Show rank and resource ID
            rank_item = QTableWidgetItem(str(rank_position))
            rank_item.setFlags(Qt.ItemIsEnabled)
            resource_item = QTableWidgetItem(str(res_id))
            resource_item.setFlags(Qt.ItemIsEnabled)

            final_table.setItem(rank_position - 1, 0, rank_item)
            final_table.setItem(rank_position - 1, 1, resource_item)

            rank_position += 1

        # Append final scores to DB
        df_scores = pd.DataFrame(df_scores_list)
        self.db_manager.append_table("final_scores", df_scores)

        final_table.resizeColumnsToContents()
        self.main_layout.addWidget(final_table)

        finish_label = QLabel("Experiment completed. Thank you!")
        self.main_layout.addWidget(finish_label)

def main():
    app = QApplication(sys.argv)
    window = ExperimentWindow(sequence_id=5) 
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

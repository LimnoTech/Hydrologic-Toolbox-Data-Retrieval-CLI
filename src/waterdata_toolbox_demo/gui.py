"""Small tkinter GUI for the Water Data ToolBox sidecar package."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.exports import format_artifact_messages
from waterdata_toolbox_demo.station_discovery import get_usgs_stations_in_bbox
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries


class WaterDataToolboxGUI:
    """Small desktop GUI for running the sidecar workflows."""

    def __init__(self, root):
        """Build both workflow sections into the provided Tk root."""
        self.root = root
        self.root.title("Water Data ToolBox Demo")

        self.create_section_frame = ttk.LabelFrame(root, text="Creating New Project")
        self.create_section_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.add_data_section_frame = ttk.LabelFrame(root, text="Adding Data to Project")
        self.add_data_section_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self._build_create_section()
        self._build_add_data_section()

    def _build_create_section(self):
        """Create controls for the bbox station discovery workflow."""
        west, south, east, north = DEMO_CONFIG["bbox"]
        self.bbox_vars = {
            "west": tk.StringVar(value=str(west)),
            "south": tk.StringVar(value=str(south)),
            "east": tk.StringVar(value=str(east)),
            "north": tk.StringVar(value=str(north)),
        }

        for row, key in enumerate(["west", "south", "east", "north"]):
            ttk.Label(self.create_section_frame, text=key.title()).grid(
                row=row, column=0, sticky="w", padx=4, pady=2
            )
            ttk.Entry(
                self.create_section_frame, textvariable=self.bbox_vars[key], width=18
            ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)

        self.create_workflow_vars = {
            workflow_type: tk.BooleanVar(value=True)
            for workflow_type in ("discharge", "gw_daily", "gw_periodic")
        }
        workflow_row = 0
        for workflow_type, var in self.create_workflow_vars.items():
            ttk.Checkbutton(
                self.create_section_frame,
                text=workflow_type,
                variable=var,
            ).grid(row=workflow_row, column=2, sticky="w", padx=6, pady=2)
            workflow_row += 1

        ttk.Button(
            self.create_section_frame,
            text="Run",
            command=self.run_create_new_project,
        ).grid(row=4, column=0, columnspan=3, sticky="ew", padx=4, pady=6)

        self.create_output = tk.Text(self.create_section_frame, width=70, height=8)
        self.create_output.grid(row=5, column=0, columnspan=3, padx=4, pady=4, sticky="nsew")

    def _build_add_data_section(self):
        """Create controls for the station-based add-data workflow."""
        example_stations = DEMO_CONFIG["example_stations"]
        self.add_workflow_var = tk.StringVar(value="discharge")
        self.station_id_var = tk.StringVar(value=example_stations["discharge"]["station_id"])
        self.parameter_code_var = tk.StringVar(
            value=example_stations["discharge"]["parameter_code"]
        )
        self.start_date_var = tk.StringVar(value=DEMO_CONFIG["date_range"][0])
        self.end_date_var = tk.StringVar(value=DEMO_CONFIG["date_range"][1])
        self.output_dir_var = tk.StringVar(value=DEMO_CONFIG["output_dir"])

        fields = [
            ("Workflow", self.add_workflow_var),
            ("Station ID", self.station_id_var),
            ("Parameter Code", self.parameter_code_var),
            ("Start Date", self.start_date_var),
            ("End Date", self.end_date_var),
            ("Output Dir", self.output_dir_var),
        ]
        for row, (label, var) in enumerate(fields):
            ttk.Label(self.add_data_section_frame, text=label).grid(
                row=row, column=0, sticky="w", padx=4, pady=2
            )
            if label == "Workflow":
                ttk.Combobox(
                    self.add_data_section_frame,
                    textvariable=var,
                    values=["discharge", "gw_daily", "gw_periodic"],
                    state="readonly",
                ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            else:
                ttk.Entry(
                    self.add_data_section_frame, textvariable=var, width=28
                ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)

        ttk.Button(
            self.add_data_section_frame,
            text="Run",
            command=self.run_add_data,
        ).grid(row=len(fields), column=0, columnspan=2, sticky="ew", padx=4, pady=6)

        self.add_data_output = tk.Text(self.add_data_section_frame, width=70, height=10)
        self.add_data_output.grid(
            row=len(fields) + 1,
            column=0,
            columnspan=2,
            padx=4,
            pady=4,
            sticky="nsew",
        )

    def run_create_new_project(self):
        """Run the create-project workflow and print station counts into the text area."""
        workflow_types = [
            workflow_type
            for workflow_type, var in self.create_workflow_vars.items()
            if var.get()
        ]
        bbox = (
            float(self.bbox_vars["west"].get()),
            float(self.bbox_vars["south"].get()),
            float(self.bbox_vars["east"].get()),
            float(self.bbox_vars["north"].get()),
        )
        results = get_usgs_stations_in_bbox(bbox, workflow_types)

        self.create_output.delete("1.0", tk.END)
        for workflow_type in workflow_types:
            frame = results[workflow_type]
            self.create_output.insert(tk.END, f"{workflow_type}: {len(frame)} stations\n")

    def run_add_data(self):
        """Run the add-data workflow and print artifact paths into the text area."""
        payload = get_usgs_timeseries(
            self.station_id_var.get(),
            self.add_workflow_var.get(),
            self.output_dir_var.get(),
            parameter_code=self.parameter_code_var.get(),
            date_range=(self.start_date_var.get(), self.end_date_var.get()),
        )

        self.add_data_output.delete("1.0", tk.END)
        self.add_data_output.insert(
            tk.END, f"{self.add_workflow_var.get()}: {len(payload['frame'])} rows\n"
        )
        for message in format_artifact_messages(payload["files"]):
            self.add_data_output.insert(tk.END, f"{message}\n")


def run_gui():
    """Launch the sidecar desktop GUI and enter the Tk event loop."""
    root = tk.Tk()
    WaterDataToolboxGUI(root)
    root.mainloop()
    return 0

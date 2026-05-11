Redevelop the existing ecological monitoring platform from a monolithic Streamlit application into a modern architecture using Vite, React, and a Python API backend.
Priorities
Priority order:


backend architecture


validation and data integrity


security and privacy


maintainability


usability and workflow simplicity


frontend polish


Do not prioritise visual complexity over usability.
Required behaviour


Ask clarifying questions until at least 95% confident in requirements


Never assume ecological logic, workflows, or reporting intent


Summarise assumptions before implementation


Identify edge cases, risks, and hidden dependencies


Challenge unclear or fragile decisions


Continuously update and refine these instructions as the project evolves


Reassess architecture and workflow decisions when new requirements emerge


Backend requirements
Design a backend-first architecture with:


modular services


API-first structure


strict separation of concerns


reusable analytical pipelines


typed schemas and validation


centralised business logic


configurable thresholds/species rules


structured logging and audit trails


automated testing support


Avoid:


duplicated logic


hardcoded spreadsheet assumptions


business logic inside UI components


tightly coupled frontend/backend code


Validation requirements
Validate:


file structure


column mappings


missing/invalid data


duplicate records


timestamp consistency


malformed Excel values


species/site mismatches


ecological range anomalies


Fail safely with readable user feedback.
Never silently modify or discard data.
Security and privacy
Assume sensitive ecological datasets.
Support:


authentication


role permissions


project isolation


encrypted storage


secure uploads


audit logging


protected APIs


controlled exports


UI/UX goals
Keep the current layout philosophy but make the platform:


simpler


cleaner


faster


easier to learn


less cluttered


workflow-driven


Prioritise:


minimal clicks


guided workflows


progressive disclosure


clear validation messages


responsive filtering


easy exports


Avoid dashboard overload.
Innovation expectations
Do not simply replicate the existing app.
Proactively suggest:


improved workflows


better visualisations


QA/QC automation


anomaly detection


suitability heatmaps


map-based navigation


ecological summaries


threshold alerts


confidence scoring


automated reporting tools


Optimise for maintainability, ecological defensibility, and ease of use.

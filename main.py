import argparse
from typing import List, Dict

import pandas as pd
from utils.utils import setup_logging
from pages.form_page import FormPage

import asyncio
from playwright.async_api import async_playwright

async def run_form_submission(csv_path: str, form_url: str) -> None:
    """Run automated form submissions from CSV using Playwright."""
    import logging
    setup_logging()
    logging.info("Starting automated form submission process.")
    results: List[Dict[str, Dict[str, str]]] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            logging.info("Playwright browser/page initialized successfully.")

            def handle_dialog(dialog):
                logging.debug("[DEBUG] Global dialog handler triggered. Accepting dialog with message: %s", dialog.message)
                asyncio.create_task(dialog.accept())
            page.on("dialog", handle_dialog)

            form_page = FormPage(page, url=form_url)

            data: pd.DataFrame = pd.read_csv(csv_path)
            logging.info(
                f"Loaded user data with {len(data)} rows "
                f"and columns: {list(data.columns)}"
            )

            for idx, row in data.iterrows():
                first_name: str = str(row["First_Name"])
                last_name: str = str(row["Last_Name"])
                email: str = str(row["Email"])
                desired_role: str = str(row["Desired_Role"])

                csv_fields = ["First_Name", "Last_Name", "Email", "Desired_Role"]
                csv_to_form = {
                    "First_Name": "First Name",
                    "Last_Name": "Last Name",
                    "Email": "Email",
                    "Desired_Role": "Desired Role"
                }

                form_fields = {
                    "First Name": first_name,
                    "Last Name": last_name,
                    "Email": email,
                    "Desired Role": desired_role
                }

                record: Dict[str, Dict[str, str]] = {}

                await form_page.open()
                present_fields = await form_page.get_present_fields()

                for csv_field in csv_fields:
                    form_key = csv_to_form[csv_field]
                    value = str(row[csv_field]) if csv_field in row else None
                    if form_key in present_fields:
                        # Only fill if present on form
                        if value and value.strip():
                            try:
                                if form_key == "First Name":
                                    logging.debug("[DEBUG] Filling First Name: %s", value)
                                    await form_page.fill_first_name(value)
                                elif form_key == "Last Name":
                                    logging.debug("[DEBUG] Filling Last Name: %s", value)
                                    await form_page.fill_last_name(value)
                                elif form_key == "Email":
                                    logging.debug("[DEBUG] Filling Email: %s", value)
                                    await form_page.fill_email(value)
                                elif form_key == "Desired Role":
                                    logging.debug("[DEBUG] Filling Desired Role: %s", value)
                                    await form_page.fill_desired_role(value)
                                record[form_key] = {"status": "successful", "value": value}
                            except Exception as exc:
                                record[form_key] = {"status": f"error: {exc}", "value": value}
                        else:
                            record[form_key] = {"status": "not submitted", "value": ""}
                    else:

                        record[form_key] = {
                            "status": "not required",
                            "value": "",
                            "explanation": "Field not present on form at runtime"
                        }

                for extra_field in row.index:
                    if extra_field not in csv_fields:
                        record[extra_field] = {"status": "not required", "value": str(row[extra_field]), "explanation": "Extra field in CSV, not required by form"}

                try:
                    logging.info(
                        f"Submitting form for {first_name} {last_name} "
                        f"({desired_role}) — Row {idx + 1}/{len(data)}"
                    )

                    logging.debug("[DEBUG] Submitting form and waiting for alert...")
                    alert_message = await form_page.submit_and_handle_alert()

                    logging.info(
                        f"Form submitted successfully for {first_name} "
                        f"{last_name} ({desired_role})"
                    )
                    logging.info(f"[ALERT] {first_name} {last_name} ({desired_role}): {alert_message}")

                except Exception as exc:
                    logging.error(f"[DEBUG] Exception during form submission: {exc}")
                    logging.error(
                        f"Error submitting form for {first_name} {last_name}: {exc}",
                        exc_info=True,
                    )

                results.append(record)
                logging.info(f"Proceeding to next user after handling alert for {first_name} {last_name}.")
                await asyncio.sleep(5)

            await browser.close()
            logging.info("Playwright browser closed successfully.")

    except Exception as exc:
        import logging
        logging.critical("Critical failure during form submissions.", exc_info=True)
        raise
    finally:
        await browser.close()
        _print_summary(results)


def _print_summary(results: List[Dict[str, Dict[str, str]]]) -> None:
    """Print a summary of all form submissions with field status."""
    import logging
    if not results:
        logging.warning("No submission records found to summarize.")
        return

    logging.info("\n" + "=" * 80)
    logging.info(f"{'FINAL SUBMISSION SUMMARY':^80}")
    logging.info("=" * 80)

    all_fields = set()
    for record in results:
        all_fields.update(record.keys())
    all_fields = list(all_fields)

    header = " | ".join([f"{field:^18}" for field in all_fields])
    logging.info(header)
    logging.info("-" * len(header))

    for record in results:
        row = []
        for field in all_fields:
            if field in record:
                status = record[field]["status"]
                value = record[field].get("value", "")
                explanation = record[field].get("explanation", "")
                if status == "successful":
                    cell = f"{value} (ok)"
                elif status == "not submitted":
                    cell = "not submitted"
                elif status == "not required":
                    cell = "not required"
                    if explanation:
                        cell += f" ({explanation})"
                else:
                    cell = status
                    if explanation:
                        cell += f" ({explanation})"
            else:
                cell = "n/a"
            row.append(f"{cell:^18}")
        logging.info(" | ".join(row))
    logging.info("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated form submission script.")
    parser.add_argument(
        "--csv_path",
        type=str,
        default="data/user_data.csv",
        help="Path to the CSV file with user data."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://doerz-automation-task.lovable.app/automation_challenge.html",
        help="URL of the form page."
    )
    args = parser.parse_args()
    asyncio.run(run_form_submission(csv_path=args.csv_path, form_url=args.url))

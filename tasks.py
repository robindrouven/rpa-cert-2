import io
import csv
import requests
from os import path
from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=1000,
    )
    open_robot_order_website()
    close_annoying_modal()
    orders = get_orders()
    submit_orders(orders)
    archive_receipts()

def open_robot_order_website():
    """Opens the RobotSpareBin Industries Inc. website."""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def close_annoying_modal():
    """Closes the annoying modal that appears when opening the website."""
    page = browser.page()
    page.click("text=I guess so...")

def get_orders():
    """Fetches the orders CSV content into memory and returns them as a table."""
    response = requests.get("https://robotsparebinindustries.com/orders.csv")
    csv_text = response.text
    
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    data = list(reader)
    
    tables = Tables()
    orders = tables.create_table(data)
    return orders

def submit_orders(orders):
    """Takes the orders and submits them on the website."""
    for order in orders:
        page = browser.page()
        
        order_number = order["Order number"]
        head_number = order["Head"]
        body_number = order["Body"]
        leg_number = order["Legs"]
        address = order["Address"]

        page.select_option("#head", str(head_number))
        page.click(f'input[name="body"][value="{body_number}"]')
        page.fill("input[placeholder='Enter the part number for the legs']", str(leg_number))
        page.fill("#address", address)
        
        screenshot_path = screenshot_robot(order_number)
        pdf_path = store_receipt_as_pdf(order_number)
        embed_screenshot_to_receipt(screenshot_path, pdf_path)
        
        page.click("#order-another")
        close_annoying_modal()

def screenshot_robot(order_number):
    """Takes a screenshot of the Robot Preview and saves it to the output folder."""
    page = browser.page()
    page.click("button:text('Preview')")
    screenshot_path = f"output/screenshots/robot_order_{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path

def store_receipt_as_pdf(order_number):
    """Orders the robot, retrying on submission error, and saves the receipt as a PDF."""
    page = browser.page()
    while True:
        page.click("#order")
        error_visible = page.locator(".alert-danger").is_visible()
        if not error_visible:
            break

    receipt_html = page.locator("#receipt").inner_html()
    pdf_path = f"output/receipts/robot_order_receipt_{order_number}.pdf"

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, pdf_path)        
    return pdf_path

def embed_screenshot_to_receipt(screenshot_path, pdf_path):
    """Embeds the robot preview screenshot into the generated PDF receipt as a new page."""
    pdf = PDF()
    files = [screenshot_path]
    pdf.add_files_to_pdf(files=files, target_document=pdf_path, append=True)

def archive_receipts():
    """Archives all PDF receipts and images from the output folders into a single ZIP file."""
    lib = Archive()
    lib.archive_folder_with_zip('./output/receipts/', './output/pdf_receipts.zip', recursive=True)
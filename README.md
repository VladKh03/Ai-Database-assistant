Database assistant built with Qwen, SQLite, FastAPI, and Gradio.
Users can read and change database records through natural language requests.
The project includes a Northwind database.

Features

Read, search, filter, and sort records.
Calculate totals and statistics using SQL joins and aggregation.
Create, update, and delete customers, products, and orders.
Create orders with multiple items.
Use recent chat history for follow-up requests.
Run up to 5 tool calls per request.
Require confirmation before deletion.
Validate tool arguments and return readable error messages.

Google Colab

Open https://colab.research.google.com/
Select Runtime > Change runtime type > T4 GPU.
A free T4 GPU can be used when available.

Run the following code in a Colab code cell:

```python
!git clone https://github.com/VladKh03/Ai-Database-assistant.git
%cd Ai-Database-assistant
!pip install -r requirements.txt
!python app.py
```

Wait for Qwen to load, then open the Gradio link shown in the output.

Manual Testing

1. Customer lookup

Request:
Show the contact name of customer ALFKI.

Expected:
Maria Anders.

2. Follow-up question

Request:
What are their phone number and city?

Expected:
Customer ALFKI. Phone: 030-0074321. City: Berlin.

3. Product lookup

Request:
Find Chai and show its product ID, unit price, and units in stock.

Expected:
Product ID: 1. Unit price: 18.00. Units in stock: 39.

4. Sorting and limit

Request:
Show the five most expensive products with their IDs and prices. Sort by price descending, then product ID ascending.

Expected:
38, Côte de Blaye, 263.50.
29, Thüringer Rostbratwurst, 123.79.
9, Mishi Kobe Niku, 97.00.
20, Sir Rodney's Marmalade, 81.00.
18, Carnarvon Tigers, 62.50.

5. Multiple tool calls

Request:
First find the customer with the most orders. Then use get_customer for that customer and show the order count, company name, contact name, and phone. Break ties by customer ID ascending.

Expected:
Customer ID: BSBEV.
Order count: 210.
Company: B's Beverages.
Contact: Victoria Ashworth.
Phone: (171) 555-1212.
Tool sequence: query_database, then get_customer.

6. Revenue calculation

Request:
For orders placed in 2022, find the top three customers by net revenue. Use each order detail unit price times quantity times (1 - discount), exclude freight, and count distinct orders. Show customer ID, company name, order count, and net revenue rounded to two decimals. Sort by revenue descending, then customer ID ascending.

Expected:
CONSH, Consolidated Holdings, 26 orders, 806385.09.
WHITC, White Clover Markets, 25 orders, 773915.02.
PARIS, Paris spécialités, 22 orders, 707175.83.

7. Product update

Request:
Change the unit price of Chai to 25.

Expected:
Product 1 has unit price 25.00 and stock 39.
No other product changes.

8. Customer creation

Request:
Create customer ZZT01 with company name Agent Test Customer, contact name Test User, city Kyiv, country Ukraine, and phone +380501111111.

Expected:
One customer ZZT01 is created with the supplied values.

9. Follow-up update

Request:
Change that customer's phone number to +380502222222.

Expected:
Customer ZZT01 has phone +380502222222.
Other fields remain unchanged.

10. Product creation

Request:
Create a product named Agent Test Product with supplier ID 1, category ID 1, unit price 25, and 20 units in stock.

Expected:
One product is created with the supplied values.
The assistant reports its database ID.

11. Order creation

Request:
Create an order for customer ZZT01 dated 2022-06-15 with freight 7. Add two units of Agent Test Product at unit price 25 with a 10 percent discount, and three units of Chai at unit price 25 with no discount.

Expected:
One order and two order items are saved in one transaction.
Agent Test Product line total: 45.00.
Chai line total: 75.00.
Total excluding freight: 120.00.
Total including freight: 127.00.
The assistant reports the new order ID.

12. Order lookup

Request:
Show the order you just created, including both items, quantities, unit prices, discounts, the total excluding freight, and the total including freight.

Expected:
The order belongs to customer ZZT01.
Agent Test Product: quantity 2, unit price 25.00, discount 10%.
Chai: quantity 3, unit price 25.00, discount 0%.
Total excluding freight: 120.00.
Total including freight: 127.00.

13. Delete request

Request:
Delete the order you just showed. Ask me for confirmation before deleting it.

Expected:
The assistant asks for confirmation for the correct order ID.
The order and both items still exist.

14. Confirm deletion

Request:
Confirm

Expected:
The order and both items are deleted.
The customer and products remain.

15. Final state check

Request:
Check whether customer ZZT01 still exists, how many orders they have, whether Agent Test Product still exists, and the current price and stock of Chai.

Expected:
Customer ZZT01 exists and has 0 orders.
Agent Test Product exists with unit price 25.00 and stock 20.
Chai exists with unit price 25.00 and stock 39.
Order creation and deletion do not change product stock.

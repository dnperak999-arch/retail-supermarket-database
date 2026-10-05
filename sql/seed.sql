INSERT INTO Role VALUES (1, 'Admin');
INSERT INTO Role VALUES (2, 'Staff');

INSERT INTO User VALUES (1, 'Anna Smith', 'anna@email.com', 'hash1', 1, 'Active');
INSERT INTO User VALUES (2, 'John Lee', 'john@email.com', 'hash2', 2, 'Active');

INSERT INTO Customer VALUES (1, 'Emily Brown', '123456789', 'emily@email.com', 'London');
INSERT INTO Customer VALUES (2, 'Michael Green', '987654321', 'michael@email.com', 'Manchester');

INSERT INTO Supplier VALUES (1, 'Fresh Foods Ltd', 'Mark Taylor', '0207000001', 'fresh@email.com');
INSERT INTO Supplier VALUES (2, 'Daily Drinks Ltd', 'Sarah White', '0207000002', 'drinks@email.com');

INSERT INTO Category VALUES (1, 'Beverages');
INSERT INTO Category VALUES (2, 'Snacks');

INSERT INTO Product VALUES (1, 'Coca-Cola', 1, 2, 1.50, '111111111', 'Soft drink');
INSERT INTO Product VALUES (2, 'Orange Juice', 1, 2, 2.00, '222222222', 'Fruit juice');
INSERT INTO Product VALUES (3, 'Potato Chips', 2, 1, 1.20, '333333333', 'Salted snack');

INSERT INTO Inventory VALUES (1, 1, 100, 10, '2026-04-02');
INSERT INTO Inventory VALUES (2, 2, 50, 10, '2026-04-02');
INSERT INTO Inventory VALUES (3, 3, 8, 10, '2026-04-02');

INSERT INTO CustomerOrder VALUES (1, 1, 1, '2026-04-02', 3.00, 'Completed');
INSERT INTO CustomerOrder VALUES (2, 2, 2, '2026-04-02', 2.40, 'Pending');

INSERT INTO OrderItem VALUES (1, 1, 1, 2, 1.50);
INSERT INTO OrderItem VALUES (2, 2, 3, 2, 1.20);

INSERT INTO Payment VALUES (1, 1, '2026-04-02', 'Card', 'Paid', 3.00);
INSERT INTO Payment VALUES (2, 2, '2026-04-02', 'Cash', 'Pending', 2.40);
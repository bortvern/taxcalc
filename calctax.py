import os
import pandas as pd
import sympy as sp


def calculate_subtotal_and_tax(total, tax_rate):
    tax_amount = total / (1 + tax_rate) * tax_rate
    subtotal = total - tax_amount
    return subtotal, round(tax_amount, 2)

def calculate_subtotals_and_tip(total, taxes, rates):
    x1, x2 = sp.symbols('x1 x2')
    t1, t2 = taxes
    r1, r2 = rates
    
    # equations
    eq2 = sp.Eq(r1 * x1, t1)
    eq3 = sp.Eq(r2 * x2, t2)
    
    # solve the equations for x1 and x2
    x1_sol = sp.solve(eq2, x1)[0]
    x2_sol = sp.solve(eq3, x2)[0]
    
    # calculate the tip
    tip = total - (x1_sol + x2_sol + t1 + t2)
    
    return float(x1_sol), float(x2_sol), float(tip)


def calculate_subtotal_and_tip(total_collection, tax_collected, tax_rate):
    # Calculate the original subtotal (pre-tax amount)
    if tax_rate > 0:
        subtotal = tax_collected / tax_rate
    else:
        subtotal = total_collection

    # Calculate the tip
    tip = total_collection - subtotal - tax_collected
    
    if tip < .01:
        tip = 0.00
    # Return the subtotal and tip
    return subtotal, tip

def read_spreadsheets(directory):
    # Create an empty list to store card purchases, tax details, and csv details
    card_purchases = []
    tax_details = []
    csv_details = []

    # Go through all files in the directory
    for filename in os.listdir(directory):
        # Check if the file is an Excel file
        if filename.endswith('.xlsx'):
            # Construct the full file path
            file_path = os.path.join(directory, filename)
            
            # Read the Excel file
            xls = pd.ExcelFile(file_path)
            
            # Check if the file has the 'Tax Details' sheet
            if 'Tax Details' in xls.sheet_names:
                # Read the 'Tax Details' sheet
                df = xls.parse('Tax Details')
                # Append the DataFrame to the tax_details list
                df['Tax Type'] = df['Tax Type'].fillna('UNSPECIFIED')
                tax_details.append(df)

        # Check if the file is a CSV file
        elif filename.endswith('.csv'):
            # Read the CSV file
            df = pd.read_csv(os.path.join(directory, filename))
            # Append the DataFrame to the csv_details list
            csv_details.append(df)

    # Concatenate all the DataFrames in the card_purchases, tax_details, and csv_details lists
    tax_details = pd.concat(tax_details)
    csv_details = pd.concat(csv_details)

    payment = csv_details[csv_details['Type'] == 'PAYMENT']

    
    #Find duplicate Transaction ID
    # Find duplicate Transaction ID
    duplicate = tax_details[tax_details.duplicated('Transaction ID', keep=False)]
    for each in duplicate['Transaction ID'].unique():
        # Call the calculate_subtotals_and_tip function with tax rates and amounts. 
        tax_rates = []
        tax_amounts = []

        for index, row in duplicate[duplicate['Transaction ID'] == each].iterrows():
            if row['Tax Type'] == 'RETAIL TAX':
                tax_rates.append(0.055)
            elif row['Tax Type'] == 'LODGE TAX':
                tax_rates.append(0.09)
            elif row['Tax Type'] == 'RESTAURANT TAX':
                tax_rates.append(0.08)
            else:
                tax_rates.append(0.0)
            tax_amounts.append(row['Tax'])
        matched_rows = tax_details[tax_details['Transaction ID'] == each]['Collected']
        subtotals = calculate_subtotals_and_tip(matched_rows.iloc[0], tax_amounts, tax_rates)
        iteration = 0
        for index, row in duplicate[duplicate['Transaction ID'] == each].iterrows():            
            if iteration == 0:
                tax_details.loc[index, 'Collected'] = subtotals[iteration] + tax_amounts[iteration] + subtotals[2]
            else:
                tax_details.loc[index, 'Collected'] = subtotals[iteration] + tax_amounts[iteration]
            iteration += 1
        
    
    # Define column widths for better layout
    transidwidth = 15
    subtotal_width = 10
    tax_width = 10
    tip_width = 10
    collected_width = 10
    tax_type_width = 15

    # Print header with improved layout
    print(f"{'TransactionID'.ljust(transidwidth)}{'Subtotal'.ljust(subtotal_width)} {'Tax'.ljust(tax_width)} {'Tip'.ljust(tip_width)} {'Collected'.ljust(collected_width)} {'Tax Type'.ljust(tax_type_width)}")
    # Init Summary Variables
    running_lodge_subtotal = 0
    running_lodge_tax = 0
    running_restaurant_subtotal = 0
    running_restaurant_tax = 0
    running_retail_subtotal = 0
    running_retail_tax = 0
    running_tip = 0
    unspecified_total = 0

    # Print each row of the merged DataFrame with improved layout
    for index, row in tax_details.iterrows():
        transaction_id = str(row['Transaction ID']).ljust(transidwidth)
        subtotal = 0
        tip = 0
        if row['Tax Type'] == 'LODGE TAX':
            subtotal, tip = calculate_subtotal_and_tip(row['Collected'], row['Tax'], 0.09)
            running_lodge_subtotal += subtotal
            running_lodge_tax += row['Tax']
            running_tip += tip
        if row['Tax Type'] == 'RESTAURANT TAX':
            subtotal, tip = calculate_subtotal_and_tip(row['Collected'], row['Tax'], 0.08)
            running_restaurant_subtotal += subtotal
            running_restaurant_tax += row['Tax']
            running_tip += tip
        if row['Tax Type'] == 'RETAIL TAX':
            subtotal, tip = calculate_subtotal_and_tip(row['Collected'], row['Tax'], 0.055)
            running_retail_subtotal += subtotal
            running_retail_tax += row['Tax']
            running_tip += tip
        if row['Tax Type'] == 'UNSPECIFIED':
            subtotal, tip = calculate_subtotal_and_tip(row['Collected'], row['Tax'], 0.0)
            unspecified_total += row['Collected']
        subtotal = "{:.2f}".format(subtotal).ljust(subtotal_width)
        tip = "{:.2f}".format(tip).ljust(tip_width)
        
        tax = "{:.2f}".format(row['Tax']).ljust(tax_width)
        collected = "{:.2f}".format(row['Collected']).ljust(collected_width)
        tax_type = str(row['Tax Type']).ljust(tax_type_width)
        print(f"{transaction_id}{subtotal} {tax} {tip} {collected} {tax_type}")
    
    for row in payment.iterrows():
        totalval = row[1]['Total'] * -1
        sub_and_tax = calculate_subtotal_and_tax(totalval, .09)
        print(f"STRIPE         {sub_and_tax[0]:.2f}     {sub_and_tax[1]:.2f}      0.00       {totalval:.2f}     LODGE TAX")

    print("\n\n")
    # Print the summary
    print(f"{('Total:').ljust(23)}${running_lodge_subtotal + running_lodge_tax + running_restaurant_subtotal + running_restaurant_tax + running_retail_subtotal + running_retail_tax + running_tip + unspecified_total:.2f}")
    print("\n")
    print(f"{'Lodge Collected:'.ljust(23)}${running_lodge_subtotal + running_lodge_tax:.2f}")
    print(f"{'Lodge Subtotal:'.ljust(23)}${running_lodge_subtotal:.2f}")
    print(f"{'Lodge Tax:'.ljust(23)}${running_lodge_tax:.2f}")
    print("\n")
    print(f"{'Restaurant Collected:'.ljust(23)}${running_restaurant_subtotal + running_restaurant_tax:.2f}")
    print(f"{'Restaurant Subtotal:'.ljust(23)}${running_restaurant_subtotal:.2f}")
    print(f"{'Restaurant Tax:'.ljust(23)}${running_restaurant_tax:.2f}")
    print("\n")
    print(f"{'Retail Collected:'.ljust(23)}${running_retail_subtotal + running_retail_tax:.2f}")
    print(f"{'Retail Subtotal:'.ljust(23)}${running_retail_subtotal:.2f}")
    print(f"{'Retail Tax:'.ljust(23)}${running_retail_tax:.2f}")
    print("\n")
    print(f"{'Tip:'.ljust(23)}${running_tip:.2f}")
    print(f"{'Unspecified:'.ljust(23)}${unspecified_total:.2f}")

    #print effective tax rates
    print(f"\n{'Lodge Tax Rate:'.ljust(23)}{running_lodge_tax/running_lodge_subtotal:.2%}")
    print(f"{'Restaurant Tax Rate:'.ljust(23)}{running_restaurant_tax/running_restaurant_subtotal:.2%}")
    print(f"{'Retail Tax Rate:'.ljust(23)}{running_retail_tax/running_retail_subtotal:.2%}")



read_spreadsheets('.')

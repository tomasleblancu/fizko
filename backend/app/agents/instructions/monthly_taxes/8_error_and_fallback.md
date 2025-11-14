## F29-Specific Cases

### No Access to F29 Data

User: "Show me my October F29"

Response:
```
I don't have direct access to your F29s.

Want me to help you:
- Understand how to read your F29 from SII
- Explain specific codes (077, 538, etc.)
- Calculate VAT or remainder with your figures
```

### Widget Fails - Text Fallback

When `show_f29_summary_widget` fails, use text format:
```
📊 F29 October 2025
- Total determined: $58,123
- Favorable remainder: $1,186,002
- Status: Received and paid

The remainder will be used as credit in November.
```

### Ambiguous Question About Amounts

User: "How much do I have to pay?"

```
To help you better, do you mean:
- Your F29 for a specific month (indicate which)
- How to calculate the amount to pay
- Understand why you pay X amount
```

### Partial F29 Data

User shares only fiscal debit and credit.

```
With debit of $X and credit of $Y:
- Net VAT = $[X-Y]
[If negative: "You'll have a remainder of $Z"]

For complete analysis I'd need:
- Previous month's remainder (code 504)
- PPM if applicable (code 062)
```

/* Marks used by the app.

   SPECLINE_ICON / SPECLINE_ICON_32 — the Specline mark (petrol ground, brackets knocked out),
   as SVG data URIs. For the app chrome, favicons and the marketing site only. Specline brands
   the application; it never appears on a generated specification.

   There is deliberately NO practice logo here, and build.py fails if one is added. The vendor's
   own mark used to be compiled in as the default seeding every practice profile, so a subscriber
   who had not yet uploaded their own issued specifications carrying it. A generated document takes
   its logo from the practice profile, or with none sets the practice's own name as a wordmark.
   Removed 7 September 2026, with the same fault in docgen/brand.py. */
const SPECLINE_ICON = "data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20512%20512%22%3E%3Crect%20width=%22512%22%20height=%22512%22%20rx=%2296%22%20fill=%22#0E6E85%22/%3E%3Cpath%20d=%22M212%20118H122V394H212M300%20118H390V394H300%22%20fill=%22none%22%20stroke=%22#FBFAF8%22%20stroke-width=%2240%22%20stroke-linejoin=%22miter%22/%3E%3C/svg%3E";
const SPECLINE_ICON_32 = "data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%2032%2032%22%3E%3Crect%20width=%2232%22%20height=%2232%22%20rx=%226%22%20fill=%22#0E6E85%22/%3E%3Cpath%20d=%22M13.5%207.5H8V24.5H13.5M18.5%207.5H24V24.5H18.5%22%20fill=%22none%22%20stroke=%22#FBFAF8%22%20stroke-width=%223%22%20stroke-linejoin=%22miter%22/%3E%3C/svg%3E";

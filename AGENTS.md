# Website instructions

## Communication

- Use short, direct sentences and common words.
- Use ASD-STE100 Simplified Technical English for reports and status messages.
- Keep the author's supplied post text unchanged unless a change is approved.
- Ask before correcting spelling, grammar, or technical claims in supplied text.

## Design references

- Read `styles.css`, `index.html`, and `first_bitcoin_payment/style.css` before changing the design.
- Use the homepage and `first_bitcoin_payment/` as the design references for new pages.
- Keep the same Open Sans font, white background, text colour, link colours, and simple layout.
- Reuse `styles.css` for shared typography and colours. Add page-specific CSS only where needed.
- Do not introduce a separate visual style for each new post.
- Use 16px body text with a 1.4 line height.
- Match article titles to the “Satoshi sends Hal Finney 10 bitcoins” heading: 1.15em, bold, line height 1.4, and zero margin.
- Use 1.15em bold section headings. Use 16px paragraph spacing, 0.5rem between list items, and 2rem between major sections.
- Use the homepage's 800px reading width for text posts. The first payment page is wider to display its data columns.
- Match the first payment page's top “Home” link: 14px, regular weight, and 24px below it.
- Leave 30px below an article header, or 24px on screens up to 700px wide.
- Use “Home”, not “Back to home”. Do not add article footers unless requested.
- Keep links underlined. On the homepage, link the topic words rather than the whole sentence.
- For the signature post, the homepage text is: Verifying a [Bitcoin transaction signature (Python)]. Include “(Python)” in the link.

## Signature verification post

- Keep the original wording, numbers, and technical claims unless a change is approved.
- Begin with the introductory text without a “Goal” heading. Then show My plan (without AI, before coding), Coding (with AI help), and What I learnt in full.
- Follow the homepage's plain text layout. Do not add boxes, arrows, tabs, expandable sections, or a row of section links.
- Reuse the shared homepage heading and list rules in `styles.css`. Keep section headings in normal case at 1.15em and content at 16px.
- Use the same solid bullet markers and 0.5rem item spacing as the homepage for What I learnt. Keep the plan numbered to show its order.
- Keep paragraphs at the full reading width without extra panel padding.
- Disable automatic word hyphenation on text posts. Let the transaction ID wrap as needed, without cutting off text or adding horizontal scrolling.
- Do not add a work-in-progress label or rename the code link without approval.
- Update the homepage learning-time total only when Arjun gives a new value.

## Editing and publishing

- Check Git status before edits and preserve existing work.
- Keep drafts local while Arjun is reviewing them. Commit and publish when he asks.
- Check the page in the browser after changes. Check section order, visible text, and links.
- Check that long transaction IDs wrap without causing horizontal scrolling.
- Keep the original article text intact when moving sections or changing markup.
- Stage only the requested files. Do not commit credentials, previews, logs, or temporary files.
- Report whether changes are local, committed, or published.

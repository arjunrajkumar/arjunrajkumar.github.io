-- Match the existing article's tight list spacing, including its byte examples.
function BulletList(list)
  for _, blocks in ipairs(list.content) do
    for i, block in ipairs(blocks) do
      if block.t == "Para" then
        blocks[i] = pandoc.Plain(block.content)
      end
    end
  end
  return list
end

function Div(div)
  if div.classes:includes("byte-example-row") then
    for i, block in ipairs(div.content) do
      if block.t == "Para" then div.content[i] = pandoc.Plain(block.content) end
    end
  end
  return div
end

-- Keep notebook cells in ordinary Markdown. Add page layout only for the website.
function Pandoc(doc)
  local sections = pandoc.List()
  local content = pandoc.List()
  local section_id = nil
  local ids = {
    ["My plan (without AI, before coding)"] = "plan",
    ["Coding (with AI help)"] = "code",
    ["What I learnt"] = "learnings"
  }
  local function finish_section()
    if #content == 0 then return end
    local attributes = {}
    if section_id then attributes["aria-labelledby"] = section_id end
    sections:insert(pandoc.Div(content, pandoc.Attr("", {"post-section"}, attributes)))
    content = pandoc.List()
  end
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and block.level == 2 then
      finish_section()
      section_id = ids[pandoc.utils.stringify(block.content)] or block.identifier
      block.identifier = section_id
      block.classes = {"subtitle"}
      -- Raw HTML prevents Quarto from also applying heading classes to the section.
      content:insert(pandoc.RawBlock("html", pandoc.write(pandoc.Pandoc({block}), "html")))
    else
      content:insert(block)
    end
  end
  finish_section()
  doc.blocks = sections
  return doc
end

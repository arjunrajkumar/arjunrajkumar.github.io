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
    -- Keep the AI exercise, saved graph and graph code in one closed disclosure.
    if section_id == "ai-exercise" then
      local exercise = pandoc.List()
      exercise:insert(pandoc.RawBlock("html",
        '<details class="ai-exercise"><summary id="ai-exercise"><strong>Exercise by AI — Adding points</strong></summary><div style="padding-top: 1rem;">'))
      -- The summary replaces the section heading.
      for i = 2, #content do
        exercise:insert(content[i])
      end
      exercise:insert(pandoc.RawBlock("html", "</div></details>"))
      content = exercise
    end
    sections:insert(pandoc.Div(content, pandoc.Attr("", {"post-section"}, attributes)))
    content = pandoc.List()
  end
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and block.level == 2 then
      finish_section()
      local heading = pandoc.utils.stringify(block.content)
      section_id = ids[heading] or block.identifier
      if heading == "Exercise by AI — Adding points" then section_id = "ai-exercise" end
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

-- Jupyter opens local chapter files. The published workbook opens the same files on GitHub.
function Link(link)
  local chapter_file = link.target:match("^book/(code%-ch%d%d/[%w_.%-]+)$")
  if chapter_file then
    link.target = "https://github.com/arjunrajkumar/programmingbitcoin/blob/master/" .. chapter_file
    return link
  end
end

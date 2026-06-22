from fastapi import FastAPI
from fastapi import Form
from fastapi.responses import HTMLResponse, RedirectResponse
import psycopg2

app = FastAPI()

def get_connection():
  return psycopg2.connect(
    dbname="homeschool_db",
    user="homeschool_user",
    password="Skywalker09!",
    host="localhost"
  )

@app.get("/", response_class=HTMLResponse)
def read_root():
  conn = get_connection()
  cur = conn.cursor()

  cur.execute("""
    SELECT
      c.id, c.name AS curriculum,
      s.id, s.name AS subject,
      d.id, d.name AS domain,
      l.id, l.level_number,
      m.id, m.name AS module,
      le.id, le.name AS lesson
    FROM curricula c
    LEFT JOIN subjects s ON s.curriculum_id = c.id
    LEFT JOIN domains d ON d.subject_id = s.id
    LEFT JOIN levels l ON l.domain_id = d.id
    LEFT JOIN modules m ON m.level_id = l.id
    LEFT JOIN lessons le ON le.module_id = m.id
    ORDER BY c.name, s.name, d.name, l.level_number, m.order_index, le.order_index;
  """)

  rows = cur.fetchall()

  conn.close()

  html = """
<script>
function toggle(id, iconId) {
  let el = document.getElementById(id);
  let icon = document.getElementById(iconId);

  if (el.style.display === 'none') {
    el.style.display = 'block';
    icon.innerHTML = "▼"; // expanded
  } else {
    el.style.display = 'none';
    icon.innerHTML = "►"; // collapsed
  }
}
</script>
<style>
.curriculum-node {
  margin-left: 0px;
  font-family: serif;
  font-weight: bold;
  font-size: 120%;
}
.subject-node {
  margin-left: 20px;
  font-family: monospace;
  font-weight: bold;
}
.domain-node {
  margin-left: 40px;
  font-family: monospace;
}
.level-node {
  margin-left: 60px;
  font-family: monospace;
}
.toggle {
  cursor: pointer;
  margin-right: 5px;
}
</style>

<h1>Curriculum</h1>

<h3>Add Subject</h3>
<form method="post" action="/add_subject">
  <input name="name" placeholder="New Subject">
  <input name="curriculum_id" value="1">
  <button type="submit">Add Subject</button>
</form>
<hr/>
"""
  
  last = {"c": None, "s": None, "d": None, "l": None, "m": None}

  for r in rows:
    c_id, c, s_id, s, d_id, d, l_id, l, m_id, m, le_id, le = r

    #Curriculum Level
    if c != last["c"]:
      # CLOSE lower levels FIRST
      if last["s"] is not None:
        html += "</div>" # close previous subject
        last["s"] = None

      if last["c"] is not None:
        html += "</div>" # close previous curriculum

      curriculum_div_id = f"cur_{c_id}"
      icon_id = f"icon_cur_{c_id}"

      html += f"""
<div class="curriculum-node"
    onclick="toggle('{curriculum_div_id}', '{icon_id}')">

    <span class="toggle" id="{icon_id}">►</span>
    {c}
</div>

<div id="{curriculum_div_id}" style="display:none;">
"""
      last["c"] = c
      last["s"] = None

    #Subject level
    if s != last["s"]:
      # CLOSE lower levels FIRST
      if last["d"] is not None:
        html += "</div>" # close previous domain
        last["d"] = None

      if last["s"] is not None:
        html += "</div>" # close previous subject

      subject_div_id = f"sub_{s_id}"
      icon_id = f"icon_sub_{s_id}"

      html += f"""
<div class="subject-node"
    onclick="toggle('{subject_div_id}', '{icon_id}')">

    <span class="toggle" id="{icon_id}">►</span>
    {s}
</div>

<div id="{subject_div_id}" style="display:none;">
"""
      last["s"] = s
      last["d"] = None

    #Domain level
    if d != last["d"]:
      #CLOSE lower levels FIRST
      if last["l"] is not None:
        html += "</div>" # close previous level
        last["l"] = None

      if last["d"] is not None:
        html += "</div>" # close previous domain

      domain_div_id = f"dom_{d_id}"
      icon_id = f"icon_dom_{d_id}"

      html += f"""
<div class="domain-node"
    onclick="toggle('{domain_div_id}', '{icon_id}')">

    <span class="toggle" id="{icon_id}">►</span>
      {d}
</div>

<div id="{domain_div_id}" style="display:none;">
"""
      last["d"] = d
      last["l"] = None

    #Level level
    if l != last["l"]:
      #CLOSE lower levels FIRST
      if last["m"] is not None:
        html += "</div>" # close previous module
        last["m"] = None
      
      if last["l"] is not None:
        html += "</div>" # close prebious level

      level_div_id = f"lev_{l_id}"
      icon_id = f"icon_lev_{l_id}"

      html += f"""
<div class="level-node"
      onclick="toggle('{level_div_id}', '{icon_id}')">

      <span class="toggle" id="{icon_id}">►</span>
        Level {l}
</div>

<div id="{level_div_id}" style="display:none;">
"""
      last["l"] = l
      last["m"] = None

    if m != last["m"]:
      html += f"<div style='margin-left:80px'>{m}</div>"
      last["m"] = m

    if le:
      html += f"<div style='margin-left:100px'>- {le}</div>"

  if last["l"] is not None:
    html += "</div>"

  if last["d"] is not None:
    html += "</div>"

  if last["s"] is not None:
    html += "</div>"

  if last["c"] is not None:
    html += "</div>"

  return html

@app.post("/add_subject")
def add_subject(name: str = Form(...), curriculum_id: int = Form(...)):
  conn = get_connection()
  cur = conn.cursor()

  cur.execute(
    "INSERT INTO subjects (name, curriculum_id) VALUES (%s, %s)",
    (name, curriculum_id)
  )

  conn.commit()
  conn.close()

  return RedirectResponse("/", status_code=303)

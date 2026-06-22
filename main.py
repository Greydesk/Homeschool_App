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

  tree = {}

  for r in rows:
    c_id, c, s_id, s, d_id, d, l_id, l, m_id, m, le_id, le = r

    if c_id not in tree:
      tree[c_id] = {
        "name": c,
        "subjects": {}
      }

    if s_id is None:
      continue

    subjects = tree[c_id]["subjects"]

    if s_id not in subjects:
      subjects[s_id] = {
        "name": s,
        "domains": {}
      }

    if d_id is None:
      continue

    domains = subjects[s_id]["domains"]
    
    if d_id not in domains:
      domains[d_id] = {
        "name": d,
        "levels": {}
      }

    if l_id is None:
      continue

    levels = domains[d_id]["levels"]

    if l_id not in levels:
      levels[l_id] = {
        "number": l,
        "modules": {}
      }
    
    if m_id is None:
      continue

    modules = levels[l_id]["modules"]

    if m_id not in modules:
      modules[m_id] = {
        "name": m,
        "lessons": []
      }

    if le_id is not None:
      continue

    modules[m_id]["lessons"][le_id] = le

    lessons = modules[m_id]["lessons"]

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
  
  for c_id, c_data in tree.items():
    cur_div = f"cur_{c_id}"
    icon = f"icon_cur_{c_id}"

    html += f"""
<div class="curriculum-node" onclick="toggle('{cur_div}', '{icon}')" >
  <span class="toggle" id="{icon}">►</span>
  {c_data['name']}
</div>
<div id="{cur_div}" style="display:none;">
"""
    for s_id, s_data in c_data["subjects"].items():
      sub_div = f"sub_{s_id}"
      icon = f"icon_sub_{s_id}"

      html += f"""
<div class="subject-node" onclick="toggle('{sub_div}', '{icon}')" >
    <span class="toggle" id="{icon}">►</span>
    {s_data['name']}
</div>

<div id="{sub_div}" style="display:none;">
"""
      
      for d_id, d_data in s_data["domains"].items():
        dom_div = f"dom_{d_id}"
        icon = f"icon_dom_{d_id}"

        html += f"""
<div class="domain-node" onclick="toggle('{dom_div}', '{icon}')" >
    <span class="toggle" id="{icon}">►</span>
    {d_data['name']}
</div>

<div id="{dom_div}" style="display:none;">
"""
        
        for l_id, l_data in d_data["levels"].items():
          lev_div = f"lev_{l_id}"
          icon = f"icon_lev_{l_id}"

          html += f"""
<div class="level-node" onclick="toggle('{lev_div}', '{icon}')" >
    <span class="toggle" id="{icon}">►</span>
    Level {l_data['number']}
</div>

<div id="{lev_div}" style="display:none;">
"""
          
          for m_id, m_data in l_data["modules"].items():
            mod_div = f"mod_{m_id}"
            icon = f"icon_mod_{m_id}"

            html += f"""
<div class="level-node" onclick="toggle('{mod_div}', '{icon}')" >
    <span class="toggle" id="{icon}">►</span>
    {m_data['name']}
</div>

<div id="{mod_div}" style="display:none;">
"""
            
            for le_id, le_name in m_data["lessons"].items():
              html += f"<div class='level-node'>{le_name}</div>"

            html += "</div>" # module
          html += "</div>" # level
        html += "</div>" # domain
      html += "</div>" # subject
    html += "</div>" # curriculum
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

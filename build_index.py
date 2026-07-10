"""
Generates a self-contained index.html that embeds app.py and data_provider.py
directly — eliminating browser cache issues with separate file fetches.
"""

with open("app.py", "r", encoding="utf-8") as f:
    app_content = f.read()

with open("data_provider.py", "r", encoding="utf-8") as f:
    dp_content = f.read()

# Safety check: <script> tags in HTML stop at </script — make sure Python
# code doesn't contain that string.
assert "</script" not in app_content.lower(), "app.py contains </script!"
assert "</script" not in dp_content.lower(), "data_provider.py contains </script!"

HEADER = """\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Real-Time Data Analytics Dashboard</title>
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.58.0/build/stlite.css"
    />
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
      #loading {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 100vh; background-color: #0e1117;
        color: #ffffff; font-family: 'Outfit', sans-serif;
        text-align: center; padding: 20px;
      }
      .spinner {
        border: 4px solid rgba(255,255,255,0.1); width: 60px; height: 60px;
        border-radius: 50%; border-left-color: #6366f1;
        animation: spin 1s linear infinite; margin-bottom: 25px;
        box-shadow: 0 0 15px rgba(99,102,241,0.2);
      }
      @keyframes spin { 0%{ transform: rotate(0deg); } 100%{ transform: rotate(360deg); } }
      h2 { font-weight: 600; margin-bottom: 8px; letter-spacing: -0.01em; }
      p  { color: #9ca3af; font-size: 0.95rem; max-width: 400px; line-height: 1.5; }
    </style>
  </head>
  <body>
    <div id="loading">
      <div class="spinner"></div>
      <h2>Starting Dashboard Environment...</h2>
      <p>
        Initializing Python WebAssembly (Pyodide) directly inside your browser.
        This may take a few seconds on the first load.
      </p>
    </div>
    <div id="root"></div>

    <!--
      Python source files are embedded directly in this HTML file.
      This eliminates all browser/CDN cache issues with separate fetches.
    -->
    <script type="text/plain" id="app-py">
"""

MIDDLE = """\
    </script>

    <script type="text/plain" id="dp-py">
"""

FOOTER = """\
    </script>

    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.58.0/build/stlite.js"></script>
    <script>
      try {
        var appPy = document.getElementById("app-py").textContent;
        var dpPy  = document.getElementById("dp-py").textContent;

        document.getElementById("loading").style.display = "none";

        stlite.mount(
          {
            requirements: ["plotly", "requests"],
            entrypoint: "app.py",
            files: {
              "app.py":           appPy,
              "data_provider.py": dpPy
            },
          },
          document.getElementById("root")
        );
      } catch (err) {
        console.error(err);
        document.getElementById("loading").innerHTML =
          "<div style='font-size:3rem;margin-bottom:20px;'>&#x26A0;&#xFE0F;</div>" +
          "<h2 style='color:#ef4444;'>Failed to start dashboard</h2>" +
          "<p>" + (err.message || String(err)) + "</p>" +
          "<p style='font-size:0.8rem;margin-top:20px;color:#6b7280;'>Check the browser console for details.</p>";
      }
    </script>
  </body>
</html>
"""

html = HEADER + app_content + MIDDLE + dp_content + FOOTER

with open("index.html", "w", encoding="utf-8", newline="\n") as f:
    f.write(html)

print(f"index.html written successfully — {len(html):,} bytes")

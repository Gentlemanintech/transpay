from flask import Flask, render_template, request


app = Flask(__name__)

@app.route("/")
def index():
    heading = "Did he get the"
    para = "This is my Webpage"

    return render_template("index.html", heading=heading, para=para)



if __name__ == "__main__":
    app.run(debug=True)

import os
from cs50 import SQL
from flask import Flask,render_template,redirect,request,session,flash,Blueprint
from flask_session import Session
from helpers import  login_required
from jinja2 import TemplateNotFound



app = Flask(__name__,static_folder='static')

db = SQL("sqlite:///mydb.db")

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


pages_bp = Blueprint('pages', __name__)
@pages_bp.route('/<page_name>',methods=['GET', 'POST'])
def render_page(page_name = "index"):
    try:
        return render_template('pages/{page_name}.html')
    except TemplateNotFound:
        return render_template("404.html")


app.register_blueprint(pages_bp)



if __name__ == '__main__':
    app.run(debug=True)


@app.route("/userinfo", methods=["POST"])
@login_required
def userinfo():
    query_user = db.execute("SELECT * FROM customer WHERE id =?", session["user_id"])
    return render_template("profile.html",query_user=query_user)

@app.route("/edituserinfo", methods=["POST","GET"])
@login_required
def edituserinfo():
    if request.method == "POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        db.execute("UPDATE customer SET firstname =?, lastname =?, email =? WHERE id =?", firstname,lastname,email,session["user_id"])
        return redirect("/profile")

@app.route("/changepassword", methods=["POST"])
@login_required
def changepassword():
    if request.method == "POST":
        newpassword = request.form.get("newpassword")
        oldpassword = request.form.get("oldpassword")
        checkoldpassword = db.execute("SELECT password FROM customer WHERE id =?", session["user_id"])
        if str(checkoldpassword[0]["password"]) == str(oldpassword):
            db.execute("UPDATE customer SET password =? WHERE id =?", newpassword, session["user_id"])
            return redirect("/logout")
        else:
            flash("پسورد قدیمی درست نمی باشد!")
            return redirect("/profilesetting")



@app.route("/flightgrid",methods=["GET"])
def flight_grid():
    query_flight = db.execute("SELECT * FROM flight")
    return render_template("flight-grid.html",query_flight=query_flight)

@app.route("/dashboard",methods=["GET"])
@login_required
def dashboard():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?",session["user_id"])
    return render_template("dashboard.html",query_user=query_user)

@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():

    query_user = db.execute("SELECT * FROM customer WHERE id =?", session["user_id"])

    if query_user[0]["flightid"] is not None and query_user[0]["hotelid"] is not None:
        hotelid = query_user[0]["hotelid"]
        query_hotel = db.execute("SELECT * FROM hotel WHERE id =?", hotelid)
        flightid = query_user[0]["flightid"]
        query_flight = db.execute("SELECT * FROM flight WHERE id =?", flightid)
        return render_template("profile.html",query_hotel=query_hotel,query_flight=query_flight,query_user=query_user)

    if query_user[0]["flightid"] is not None:
        flightid = query_user[0]["flightid"]
        query_flight = db.execute("SELECT * FROM flight WHERE id =?", flightid)
        return render_template("profile.html",query_flight=query_flight,query_user=query_user)

    if query_user[0]["hotelid"] is not None:
        hotelid = query_user[0]["hotelid"]
        query_hotel = db.execute("SELECT * FROM hotel WHERE id =?", hotelid)
        return render_template("profile.html",query_hotel=query_hotel,query_user=query_user)

    if query_user[0]["flightid"] is None and query_user[0]["hotelid"] is None:
        return render_template("profile.html",query_user=query_user)


@app.route("/wallet", methods=["POST"])
@login_required
def wallet():
    if request.method == "POST":
        customer = db.execute("SELECT * FROM customer WHERE id =?", session["user_id"])
        sum = int(request.form.get("increase")) + int(customer[0]["balance"])
        db.execute("UPDATE customer SET balance =? WHERE id =?", sum, session["user_id"])
        flash("عملیات با موفقیت انجام شد!")
        return redirect("/profilewallet")


@app.route("/login", methods=["GET","POST"])
def login():

    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            message="Invalid email or password"
            return render_template("login.html",message=message)
        else:
            user = db.execute("SELECT * FROM customer WHERE email =? AND password =?", email, password)
            if user:
                session["user_id"] = user[0]["id"]
                return redirect("/")
            else:
                message="Invalid email or password"
                return render_template("login.html",message=message)


@app.route("/signup",methods=["GET","POST"])
def signup():

    session.clear()

    if request.method == "GET":
        return render_template("register.html")
    else:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        if not firstname or not lastname or not email or not password:
            return render_template("register.html",message="All fields are required")

        row = db.execute("SELECT * FROM customer WHERE email =?", email)
        if row:
            return render_template("register.html",message="Email already exists")
        else:
            firstname = captal(firstname)
            lastname = captal(lastname) 
            id = db.execute("INSERT INTO customer (firstname, lastname, email, password) VALUES (?,?,?,?)", firstname, lastname, email, password)
            session["user_id"] = id
            return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/",methods=["GET"])
def index():
    hotels = db.execute("SELECT * FROM hotel")
    return render_template("index.html",hotels=hotels)


@app.route("/details", methods=['POST'])
def details(message = "not send name"):
    if not request.form.get("hotel_name"):
        return render_template("details.html",message=message)

    details = db.execute("SELECT * FROM hotel WHERE name = ?",request.form.get("hotel_name"))
    return render_template("details.html",details=details)

@app.route("/reserve",methods=["POST"])
@login_required
def reserve():
    customer = db.execute("SELECT * FROM customer WHERE id =?",session["user_id"])
    balance = int(request.form.get("price"))
    price = int(customer[0]["balance"]) - ( balance * int(request.form.get("number")) )
    db.execute("UPDATE customer SET balance =?,hotelid=? WHERE id =?",price,request.form.get("hotelid"),session["user_id"])
    get = db.execute("SELECT * FROM hotel WHERE name = ?",request.form.get("hotel_name"))
    room = db.execute("UPDATE hotel SET numberofroom = ? WHERE name = ?",int(get[0]["numberofroom"]) - int(request.form.get("number")),request.form.get("hotel_name"))
    flash("The hotel was successfully booked.")
    return redirect("/profile")


@app.route("/filter",methods=["POST"])
def filter_hotels():
    city = request.form.get("city").title()
    hotels = db.execute("SELECT * FROM hotel WHERE city = ?",city)
    if len(hotels) < 1:
        return index()
    if hotels is not None:
        return render_template("index.html",hotels=hotels)


#func haye hotel vase ghaleb

@app.route("/hotelgrid",methods=["GET", "POST"])
def hotelgrid():
    return render_template("hotel-grid.html")

@app.route("/hotelfullwidth",methods=["GET", "POST"])
def hotelfullwidth():
    return render_template("hotel-full-width.html")


@app.route("/hotelroomgrid",methods=["GET"])
def hotelroomgrid():
    return render_template("hotel-room-grid.html")

@app.route("/hotelroomlist",methods=["GET"])
def hotelroomlist():
    return render_template("hotel-room-list.html")

@app.route("/hotelroomfullwidth",methods=["GET"])
def hotelroomfullwidth():
    return render_template("hotel-room-full-width.html")

@app.route("/hotelroomsingle",methods=["GET"])
def hotelroomsingle():
    return render_template("hotel-room-single.html")

@app.route("/hotelroomsearchresult",methods=["GET"])
def hotelroomssearchresult():
    return render_template("hotel-room-search-result.html")



@app.route("/hotelroomadd",methods=["GET", "POST"])
@login_required
def hotelroomadd():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("hotel-room-add.html",query_user=query_user)


@app.route("/hotelsingle",methods=["GET"])
def hotelsingle():
    return render_template("hotel-single.html")

@app.route("/hotelbooking",methods=["GET"])
def hotelbooking():
    return render_template("hotel-booking.html")

@app.route("/hotelsearchresult",methods=["GET"])
def hotelsearchresult():
    return render_template("hotel-search-result.html")


@app.route("/hoteladd",methods=["GET","POST"])
@login_required
def hoteladd():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("hotel-add.html",query_user=query_user)

@app.route("/destination",methods=["GET"])
def destination():
    return render_template("destination.html")


@app.route("/career",methods=["GET"])
def career():
    return render_template("career.html")

@app.route("/careersingle",methods=["GET"])
def careersingle():
    return render_template("career-single.html")

@app.route("/becomeexpert",methods=["GET"])
def becomeexpert():
    return render_template("become-expert.html")

@app.route("/cart",methods=["GET"])
@login_required
def cart():
    return render_template("cart.html")

@app.route("/checkout",methods=["GET"])
def checkout():
    return render_template("checkout.html")


@app.route("/bookingconfirm",methods=["GET"])
def bookingconfirm():
    return render_template("booking-confirm.html")





# function haye ghesmate safahat vase ghaleb
@app.route("/forgotpassword",methods=["GET"])
def forgotpassword():
    return render_template("forgot-password.html")


@app.route("/profilelisting",methods=["GET", "POST"])
@login_required
def profilelisting():   
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-listing.html",query_user=query_user)


@app.route("/profilebooking",methods=["GET", "POST"])
@login_required
def profilebooking():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-booking.html",query_user=query_user)


@app.route("/profilebookinghistory",methods=["GET"])
@login_required
def profilebookinghistory():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-booking-history.html",query_user=query_user)

@app.route("/profilewishlist",methods=["GET"])
@login_required
def profilewishlist():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-wishlist.html",query_user=query_user)


@app.route("/profilewallet",methods=["GET"])
@login_required
def profilewallet():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-wallet.html",query_user=query_user)


@app.route("/profilemessage",methods=["GET"])
@login_required
def profilemessage():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-message.html",query_user=query_user)

@app.route("/profilenotification",methods=["GET"])
@login_required
def profilenotifications():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-notification.html",query_user=query_user)

@app.route("/profilesetting",methods=["GET"])
@login_required
def profilesetting():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("profile-setting.html",query_user=query_user)

@app.route("/about",methods=["GET"])
def about():
    return render_template("about.html")

@app.route("/pricing",methods=["GET"])
def pricing():
    return render_template("pricing.html")

@app.route("/team",methods=["GET"])
def team():
    return render_template("team.html")

@app.route("/service",methods=["GET"])
def service():
    return render_template("service.html")

@app.route("/servicesingle",methods=["GET"])
def servicesingle():
    return render_template("service-single.html")


@app.route("/gallery",methods=["GET"])
def gallery():
    return render_template("gallery.html")


@app.route("/contact",methods=["GET"])
def contact():
    return render_template("contact.html")


@app.route("/blog",methods=["GET"])
def blog():
    return render_template("blog.html")

@app.route("/blogsingle",methods=["GET"])
def blogsingle():
    return render_template("blog-single.html")

@app.route("/faq",methods=["GET"])
def faq():
    return render_template("faq.html")


@app.route("/testimonial",methods=["GET"])
def testimonial():
    return render_template("testimonial.html")

@app.route("/404",methods=["GET"])
def error404():
    return render_template("404.html")

@app.route("/comingsoon",methods=["GET"])
def comingsoon():
    return render_template("coming-soon.html")


@app.route("/terms",methods=["GET"])
def terms():
    return render_template("terms.html")

@app.route("/privacy",methods=["GET"])
def privacy():
    return render_template("privacy.html")

@app.route("/activitygrid",methods=["GET"])
def activitygrid():
    return render_template("activity-grid.html")




@app.route("/activitylist",methods=["GET"])
def activitylist():
    return render_template("activity-list.html")

@app.route("/activityfullwidth",methods=["GET"])
def activityfullwidth():
    return render_template("activity-full-width.html")

@app.route("/activitysingle",methods=["GET"])
def activitysingle():
    return render_template("activity-single.html")

@app.route("/activitybooking",methods=["GET"])
def activitybooking():
    return render_template("activity-booking.html")

@app.route("/activitysearchresult",methods=["GET"])
def activitysearchresult():
    return render_template("activity-search-result.html")

@app.route("/activityadd",methods=["GET","POST"])
@login_required
def activityadd():
    query_user = db.execute("SELECT * FROM customer WHERE id=?",session["user_id"])
    return render_template("activity-add.html",query_user=query_user)


@app.route("/cargrid",methods=["GET"])
def cargrid():
    return render_template("car-grid.html")

@app.route("/carlist",methods=["GET"])
def carlist():
    return render_template("car-list.html")

@app.route("/carfullwidth",methods=["GET"])
def carfullwidth():
    return render_template("car-full-width.html")

@app.route("/carsingle",methods=["GET"])
def carsingle():
    return render_template("car-single.html")

@app.route("/carbooking",methods=["GET"])
def carbooking():
    return render_template("car-booking.html")

@app.route("/carsearchresult",methods=["GET"])
def carsearchresult():
    return render_template("car-search-result.html")

@app.route("/caradd",methods=["GET","POST"])
@login_required
def caradd():
    query_user = db.execute("SELECT * FROM customer WHERE id=?",session["user_id"])
    return render_template("car-add.html",query_user=query_user)


@app.route("/cruisegrid",methods=["GET"])
def cruisegrid():
    return render_template("cruise-grid.html")

@app.route("/cruiselist",methods=["GET"])
def cruiselist():
    return render_template("cruise-list.html")

@app.route("/cruisefullwidth",methods=["GET"])
def cruisefullwidth():
    return render_template("cruise-full-width.html")

@app.route("/cruisesingle",methods=["GET"])
def cruisesingle():
    return render_template("cruise-single.html")

@app.route("/cruisebooking",methods=["GET"])
def cruisebooking():
    return render_template("cruise-booking.html")

@app.route("/cruisesearchresult",methods=["GET"])
def cruisesearchresult():
    return render_template("cruise-search-result.html")

@app.route("/cruiseadd",methods=["POST","GET"])
@login_required
def cruiseadd():
    query_user = db.execute("SELECT * FROM customer WHERE id=?",session["user_id"])
    return render_template("cruise-add.html",query_user=query_user)


@app.route("/tourgrid",methods=["GET"])
def tourgrid():	
    return render_template("tour-grid.html")


@app.route("/tourlist",methods=["GET"])
def tourlist():
    return render_template("tour-list.html")

@app.route("/tourfullwidth",methods=["GET"])
def tourfullwidth():
    return render_template("tour-full-width.html")

@app.route("/toursingle",methods=["GET"])
def toursingle():
    return render_template("tour-single.html")

@app.route("/tourbooking",methods=["GET"])
def tourbooking():
    return render_template("tour-booking.html")

@app.route("/toursearchresult",methods=["GET"])
def toursearchresult():
    return render_template("tour-search-result.html")


@app.route("/touradd",methods=["GET","POST"])
@login_required
def touradd():
    query_user = db.execute("SELECT * FROM customer WHERE id=?",session["user_id"])
    return render_template("tour-add.html",query_user=query_user)





#func haye flight vase ghaleb
@app.route("/flightadd",methods=["GET","POST"])
@login_required
def flightadd():
    query_user = db.execute("SELECT * FROM customer WHERE id = ?", session["user_id"])
    return render_template("flight-add.html",query_user=query_user)


@app.route("/flightlist",methods=["GET","POST"])
def flightlist():
        flights = db.execute("SELECT * FROM flight")
        return render_template("flight-list.html",flights=flights)

@app.route("/flightfullwidth",methods=["GET","POST"])
def flightfullwidth():
    return render_template("flight-full-width.html")


@app.route("/flightsingle", methods=["GET","POST"])
def flightsingle():
    return render_template("flight-single.html")

@app.route("/flightbooking",methods=["GET"])
def flightbooking():
    return render_template("flight-booking.html")

@app.route("/flightsearchresult",methods=["GET"])
def flightsearchresult():
    return render_template("flight-search-result.html")

###############################################################################

@app.route("/flight",methods=["GET","POST"])
def flight():
        flights = db.execute("SELECT * FROM flight")
        return render_template("flight.html",flights=flights)

@app.route("/filterflights",methods=["POST"])
def filter_flights():
    if len(request.form.get("airline")) and len(request.form.get("origin")) and len(request.form.get("destination")) > 1:
        origin = captal(request.form.get("origin"))
        destination = captal(request.form.get("destination"))
        airlines = captal(request.form.get("airline"))
        flights = db.execute("SELECT * FROM flight WHERE origin =? AND destination =? AND airline=?",origin,destination,airlines)
        if len(flights) < 1:
            message = "There is no airline with this title with specified origin and destination."
            return flight(message)
        else:
            return render_template("flight.html",flights=flights)

    if len(request.form.get("airline")) > 0:
        airlines = captal(request.form.get("airline"))
        flights = db.execute("SELECT * FROM flight WHERE airline =?",airlines)
        if len(flights) < 1:
            message = "There is no airline with the given name."
            return flight(message)
        if flights is not None:
            return render_template("flight.html",flights=flights)

    if not request.form.get("origin") or not request.form.get("destination"):
        message = "Please enter origin and destination"
        return flight(message)
    else:
        origin = captal(request.form.get("origin"))
        destination = captal(request.form.get("destination"))
        flights = db.execute("SELECT * FROM flight WHERE origin =? AND destination =?",origin,destination)
        if len(flights) < 1:
            message = "There is no flight with the given origin and destination."
            return flight(message)
        else:
            return render_template("flight.html",flights=flights)


@app.route("/flightdetail",methods=["POST"])
def flightdetail():
    rows = db.execute("SELECT * FROM flight WHERE photoairline =? AND airline=? AND origin=? AND destination=?",request.form.get("photoairline"),request.form.get("flight_airline"),request.form.get("flight_origin"),request.form.get("flight_destination"))
    return render_template("detailsflight.html",rows=rows)

@app.route("/reserveflight",methods=["POST"])
@login_required
def reserve_flight():
    customer = db.execute("SELECT * FROM customer WHERE id =?",session["user_id"])
    balance = int(request.form.get("price"))
    price = int(customer[0]["balance"]) - balance
    db.execute("UPDATE customer SET balance =?,flightid=? WHERE id =?",price,request.form.get("flightid"),session["user_id"])
    flash("The flight was successfully booked.")
    return redirect("/profile")


def captal(words):
    output_string = ' '.join(word.capitalize() for word in words.split())
    return output_string






from flask import Flask, render_template ,redirect ,url_for,request , session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer,String
from sqlalchemy.orm import Mapped , mapped_column
import smtplib
from random import randint
from werkzeug.security import generate_password_hash , check_password_hash
from flask_login import UserMixin ,  LoginManager,  login_required , login_user , logout_user , current_user
import phonenumbers 
import resend 
from dotenv import load_dotenv
import os 
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATA_BASE")
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)
resend.api_key = os.getenv("RENDER_KEY")

login_manager = LoginManager()
login_manager.init_app(app)

my_mail = "adebayomuhammed99@gmail.com"
my_password =os.getenv("EMAIL_PASSWORD")


class Customers (db.Model , UserMixin):
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    First_name : Mapped[str]= mapped_column(String(250), nullable=False)
    Last_name  : Mapped[str]= mapped_column(String(250), nullable=False)
    Birth_date: Mapped[str]= mapped_column(String(250), nullable=False)
    Gmail : Mapped[str] = mapped_column(String(250),nullable=False , unique=True)
    Phone_number : Mapped[str] = mapped_column (String(250), nullable=False)
    Password : Mapped[str] = mapped_column (String(250), nullable=False)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Customers.query.get(int(user_id))


@app.route("/" , methods= ["POST","GET"])
def login ():
    if request.method == "POST":
         information = request.form['info']
         password = request.form['password']
         if '@' in information :
             session['email'] = information.lower()
         else:
             message = "ENTER A VALID EMAIL ADDRESS "
             return render_template ('login.html' , error = message)  
         user = Customers.query.filter((Customers.Gmail == information) |( Customers.Phone_number == information)).first()
         otp =str(randint(1000,9999)) 
         session["otp"] = otp
         session["password"] = password
         email_text = f'''below is your one-time passcode (OTP) to complete your authentication:

👉 {otp}



⚠️ Do not share this code with anyone for security reasons.

If you did not request this code, please ignore this email.

---

Mini Jumia Team

Fast. Simple. Reliable shopping experience.'''


         if  user: 
            if check_password_hash(user.Password, password):
               if '@' in information :
                  session['email'] = information
              
                  resend.Emails.send({
                    "from": "Mini Jumia <onboarding@resend.dev>",
                    "to": session.get('email'),
                    "subject" : f' Mini Jumia OTP Verification is {otp}',
                    "text" : email_text
                 })
              
                  session['flow'] = "login"
                  session['user_id'] = user.id
            else:
                the_error = "INCORRECT PASSWORD OR GMAIL"
                return render_template ("login.html" , message=the_error)

         else:
                   session['flow'] = "register"
    
         return redirect (url_for('verify'))    
                       
           
            

        
             
    return render_template ("login.html")


@app.route("/register", methods= ["POST", "GET"])
def information ():
    if request.method == "POST":
        user_fname = request.form['Fname']
        user_lname =  request.form['Lname']
        user_birthdate =  request.form['birthdate']
        country_code =  request.form['country_code']
        user_contact =  request.form['contact'].strip().replace(" "," ")
        user_email = session.get('email')
        user_password = session.get('password')
        user_hashed_password = generate_password_hash(user_password)
        if user_contact.startswith("+"):

         return "Do not include country code"

        if user_contact.startswith("0"):

          user_contact = user_contact[1:]

        if not country_code.startswith("+"):

         country_code = "+" + country_code

        raw_number = country_code + user_contact

        print(raw_number)

        parsed = phonenumbers.parse(raw_number, None)

        if not phonenumbers.is_valid_number(parsed):
          return "Invalid phone number ❌"



        full_phone = phonenumbers.format_number(

    parsed,

    phonenumbers.PhoneNumberFormat.E164

)
            
        new_User  = Customers (
               First_name = user_fname,
               Last_name  = user_lname,
               Birth_date = user_birthdate,
               Gmail = user_email,
               Phone_number = full_phone,
               Password = user_hashed_password
        )
        db.session.add(new_User)
        db.session.commit()
        return redirect (url_for('goods'))

        
    
    return render_template ('register.html')




@app.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "POST":

        box1 = request.form['box1']
        box2 = request.form['box2']
        box3 = request.form['box3']
        box4 = request.form['box4']

        user_otp = (box1 + box2 + box3 + box4).strip()
        user = Customers.query.get(session.get('user_id'))
        if user_otp == str(session.get('otp')).strip():
            if session.get('flow') == 'login':
                login_user(user)
                return render_template('home.html')
            elif session.get('flow') == 'register':
              return redirect (url_for("information"))

        return "WRONG OTP"   
            


    return render_template("verify.html")


@app.route("/home" , methods= ["POST", "GET"])
def goods ():
     return render_template("home.html")

if __name__ == "__main__" :
    app.run (debug=True)
 
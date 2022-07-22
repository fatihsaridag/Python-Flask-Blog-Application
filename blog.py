from ast import Pass, keyword
import email
from email import message
from hashlib import sha256
from operator import truediv
import re
from turtle import title
from typing import Text
from unicodedata import name
from unittest import result
from click import confirm
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,DateField
from passlib.hash import sha256_crypt       #Bu fonksiyon parolamızı şifrelemimizi sağlıyor.
from functools import wraps
                     
#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:                          #Sessionun içinde logged in içerisinde bir anahtar değer var mı ? Yani kullanıcı giriş yapmış demek.
              return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın!","danger")
            return redirect(url_for("login"))                           
       
    return decorated_function
#Kullanıcı Kayıt Formu  
class RegisterForm(Form) : 
    name = StringField("İsim Soyisim",validators=[validators.length(min = 4, max = 25)])                       #WTF formları
    username = StringField("Kullanıcı Adı",validators=[validators.length(min = 5, max = 35)])
    email = StringField("Email Adresi",validators=[validators.email(message="Lütfen Geçerli bir email adresi girin..")])
    password = PasswordField("Parola :" ,validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyiniz") ,       #Bunun içie eğer parola girmediyse ekrana bir hatamesajı yazdırmış oluyoruz.,
        validators.EqualTo(fieldname = "confirm",message="Parolanız uyuşmuyor.")
    ])

    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

app = Flask(__name__)     
app.secret_key = "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"                   #Kullanıcı adını ayarladık.
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)                                  #flask ile mysql arası ilişkiyi kurmuş oluyoruz.
@app.route("/")
def index() : 
    articles = [
        {"id": 1 ,"title":"Deneme1","content":"Deneme1 icerik"},
        {"id": 2 ,"title":"Deneme2","content":"Deneme2 icerik"},
        {"id": 3 ,"title":"Deneme3","content":"Deneme3 icerik"}
    
    ]
    return render_template("index.html", articles = articles)

@app.route("/about")
def about(): 
    return render_template("about.html")


#Kayıt olma
@app.route("/register",methods=["GET","POST"])
def register() : 
    form = RegisterForm(request.form)                               #Bu formun içerisine request atılmışsa formun içerisine atıyoruz. Ve bu formumuzu veritabanına kaydetmiş olacağız.
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data                               #Datamızı alıyoruz ve datamız string cinsten
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name , email, username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla kayıt oldunuz..", "success")           
        return redirect(url_for("login"))                           #Formdaki bilgileri alıp mysql veritabanına bağlanıcam ve orda sql sorgusu gerçekleştiricez.
    else:
         return render_template("register.html" , form = form)                    #Eğer request GET ise

#Login İşlemi
@app.route("/login",methods = ["GET", "POST"])
def login() :
    form = LoginForm(request.form)
    if request.method == "POST":                                    #Http requeste göre form oluşturduk ve methodumuz post ise 
        username = form.username.data                               #İçerideki bilgileri alıyoruz.
        password_entered = form.password.data                       

        cursor = mysql.connection.cursor()                          #Cursor oluşturuyoruz ve bu cursor bizim verilerimizde var mı ?
        sorgu = "Select * From users where username = %s"           #Sorgumuzu çalıştırıyoryz bu kullanıcı var mı 
        result = cursor.execute(sorgu,(username,))                  #sorgu ve kullanıcıyı çekiyoruz 
        if result > 0 :                                             #Eğer kullanıcı varsa 
            data = cursor.fetchone()                    #fetchone() ile verileri al - Database de kullanıcının bütün bilgilerini alıyoruz.
            real_password = data["password"]            # Biz burada gerçek parolamızı aldık
            if sha256_crypt.verify(password_entered,real_password):  #Eğer bizim gerçek(şifrelenmiş password ile girilen passwordu kontrol ediyoruz)
                flash("Başarıyla Giriş yaptınız...","success")       #Eğer şifreler doğruysa anasayfaya yönlendiriyoruz.
                session["logged_in"] = True                             #Sessionumuz başlatıldı ve bunu herhangi bir yerde kullanabiliriz.
                session["username"] = username
                return redirect(url_for("index"))                      
            else:
                flash("Parolanızı yanlış girdiniz.","danger")
                return redirect(url_for("login"))

        else : 
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form = form)

 #Logout İşlemi
@app.route('/logout') 
def logout() : 
    session.clear()                                 #Sessionumuz son bulmuş olacak.  
    return redirect(url_for("index"))               # Ve anasayfaya dönme işlemlerini yapıyoruz.



@app.route("/dashboard")
@login_required                                           
def dashboard() : 
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))       #Kendi usernamemize göre makaleleri aldık ve gönderdik
    if result>0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else :
     return render_template("dashboard.html")
#MAKALE EKLEME 
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle() : 
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data             
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title ,author, content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)

#MAKALE FORM
class ArticleForm(Form):
    title  = StringField("Makale Başlığı",validators=[validators.length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.length(min=10)])


@app.route("/articles")
def articles(): 
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result > 0 :
        articles = cursor.fetchall()                        #Fetchall metodu veritabanında tüm makaleleri liste içerisinde  
        return render_template("articles.html",articles = articles)  #sözlük olarak geri dönecek ve articles olarak geri göndericez
    else:
        return render_template("articles.html")


#Detay Sayfası 
@app.route("/article/<string:Id>")
def article(Id) :
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where Id = %s"
    result = cursor.execute(sorgu,(Id,))
    if result > 0 : 
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else: 
        return render_template("article.html")


#MAKALE sİLME 
@app.route("/delete/<string:Id>")
@login_required
def delete(Id): 
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and Id= %s"
    result = cursor.execute(sorgu,(session["username"],Id))
    if result > 0 :
        sorgu2 = "Delete from articles where Id = %s"
        cursor.execute(sorgu2,(Id,))
        mysql.connection.commit()
        flash("Makaleyi silme işlemi başarıyla gerçekleşti...","success")
        return redirect(url_for("dashboard"))

    else : 
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:Id>",methods  = ["GET","POST"])
@login_required
def update(Id) : 
    if request.method == "GET" : 
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where Id = %s and author = %s"
        result = cursor.execute(sorgu,(Id,session["username"]))
        if result == 0: 
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
            return redirect(url_for("index"))
        else: 
            article = cursor.fetchone()               #Makalenin şu anki halini aldık.(title,content..)
            form = ArticleForm()                
            form.title.data  = article["title"]        #Biz şu an makalemizin şu an ki değeri üzerinden formumuzu oluşturduk ve Get Requesti ile ekranda gösterdik.
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else : 
        #POST REQUEST 
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        sorgu2 = "Update articles Set title = %s , content = %s where Id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,Id))
        mysql.connection.commit()
        flash("Makale Başarıyla güncellendi", "success")
        return redirect(url_for("dashboard"))

#Arama Url
@app.route("/search",methods= ["GET","POST"])
def search() :
    if request.method == "GET" : 
        return redirect(url_for("index"))
    else: 
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%' "
        result = cursor.execute(sorgu)
        if result == 0 : 
            flash("Aranan kelimeye uygun makale bulunamadı.. ", "warning")
            return redirect(url_for("articles"))
        else : 
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if __name__ == "__main__":
    app.run(debug=True)                    


                    #DECORATER
   #dashboard çalıştırılmadan önce bu login_requireda gidicek. Ve eğer bizim sessionumuz başlatıldıysa bizim dashboardımız başlatılacak.
   #Eğer başlatılmadıysa login sayfasına gitmiş olacağız.
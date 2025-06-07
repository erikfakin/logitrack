import random
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, flash
from pony import orm
import datetime
import uuid

DB = orm.Database()

app = Flask(__name__)

class Posiljka(DB.Entity):
    id = orm.PrimaryKey(int, auto=True)
    adresa_prikupa = orm.Required(str)
    grad_prikupa = orm.Required(str)
    adresa_dostave = orm.Required(str)
    grad_dostave = orm.Required(str)
    naziv_posiljatelj = orm.Required(str)
    tel_posiljatelj = orm.Required(str)
    naziv_primatelj = orm.Required(str)
    tel_primatelj = orm.Required(str)
    status = orm.Required(str)  # "poslano", "isporuceno", "neisporuceno"
    datum_slanja = orm.Required(datetime.datetime)
    datum_isporuke = orm.Optional(datetime.datetime)
    broj_posiljke = orm.Required(str, unique=True)

DB.bind(provider='sqlite', filename='database.sqlite', create_db=True)
DB.generate_mapping(create_tables=True)


@app.get("/")
def home():
    return render_template("index.html")

@app.get("/posiljke")
def get_posiljke():
    grad_prikupa = request.args.get("grad_prikupa")
    grad_dostave = request.args.get("grad_dostave")
    status = request.args.get("status")
    sort_by = request.args.get("sort_by")

    try:
        with orm.db_session:
            
            posiljke = Posiljka.select()
            
            if grad_prikupa:
                posiljke = posiljke.filter(lambda p: p.grad_prikupa == grad_prikupa)
            if grad_dostave:
                posiljke = posiljke.filter(lambda p: p.grad_dostave == grad_dostave)
            if status:
                posiljke = posiljke.filter(lambda p: p.status == status)

            if sort_by == "datum_slanja":
                posiljke = posiljke.order_by(lambda p: orm.desc(p.datum_slanja))
            elif sort_by == "datum_isporuke":
                posiljke = posiljke.order_by(lambda p: orm.desc(p.datum_isporuke))
            elif sort_by == "grad_prikupa":
                posiljke = posiljke.order_by(Posiljka.grad_prikupa)
            elif sort_by == "grad_dostave":
                posiljke = posiljke.order_by(Posiljka.grad_dostave)

            return render_template("posiljke.html", posiljke=posiljke)
        
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )

@app.get("/posiljka/<int:id>")
def get_posiljka(id):
    try:
        with orm.db_session:
            posiljka = Posiljka.get(id=id)
            if posiljka:
                return render_template("posiljka.html", posiljka=posiljka)
            else:
                flash("Pošiljka nije pronađena.", "error")
                return redirect(url_for('home'))
                
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )

@app.get("/posiljka/create")
def create_posiljka():
    return render_template("create_posiljka.html")

@app.post("/posiljka")
def store_posiljka():
    data = request.form.to_dict()
    broj_posiljke = generate_broj_posiljke()
    try:
        with orm.db_session:
            posiljka = Posiljka(
                adresa_prikupa=data["adresa_prikupa"],
                grad_prikupa=data["grad_prikupa"],
                adresa_dostave=data["adresa_dostave"],
                grad_dostave=data["grad_dostave"],
                naziv_posiljatelj=data["naziv_posiljatelj"],
                tel_posiljatelj=data["tel_posiljatelj"],
                naziv_primatelj=data["naziv_primatelj"],
                tel_primatelj=data["tel_primatelj"],
                status= "poslano", 
                datum_slanja=datetime.datetime.now(),
                datum_isporuke=None,
                broj_posiljke=broj_posiljke
            )
            flash(f"Pošiljka {broj_posiljke} je uspješno kreirana.", "success")
            return render_template("hvala.html", posiljka=posiljka)

    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )


@app.get("/posiljka/track")
def track_posiljka():
    broj_posiljke = request.args.get("broj_posiljke")
    if not broj_posiljke:
        return render_template('track_posiljka.html')
    try:
        with orm.db_session:
            posiljka = Posiljka.get(broj_posiljke=broj_posiljke)
            if posiljka:
                return render_template('posiljka_status.html', posiljka=posiljka)
            else:
                flash("Pošiljka nije pronađena.", "error")
                return render_template('track_posiljka.html')
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )

@app.get("/posiljka/edit/<int:id>")
def edit_posiljka(id):
    print(f"Editing posiljka with id: {id}")
    try:
        with orm.db_session:
            posiljka = Posiljka[id]
            if posiljka:
                return render_template("edit_posiljka.html", posiljka=posiljka)
            else:
                flash("Pošiljka nije pronađena.", "error")
                return redirect(url_for('get_posiljke'))
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )
    

@app.post("/posiljka/<int:id>")
def update_posiljka(id):
    data = request.form.to_dict()
    try:
        with orm.db_session:
            posiljka = Posiljka[id]
            if posiljka:

                if "adresa_dostave" in data:
                    posiljka.adresa_dostave = data["adresa_dostave"]
                if "grad_dostave" in data:
                    posiljka.grad_dostave = data["grad_dostave"]
                if "naziv_posiljatelj" in data:
                    posiljka.naziv_posiljatelj = data["naziv_posiljatelj"]
                if "tel_posiljatelj" in data:
                    posiljka.tel_posiljatelj = data["tel_posiljatelj"]
                if "naziv_primatelj" in data:
                    posiljka.naziv_primatelj = data["naziv_primatelj"]
                if "tel_primatelj" in data:
                    posiljka.tel_primatelj = data["tel_primatelj"]
                
                flash("Pošiljka je uspješno ažurirana.", "success")
                return get_posiljka(id)
            else:
                return make_response(jsonify({"error": "Posiljka not found"}), 404)
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )
    
@app.post("/posiljka/delete/<int:id>")
def delete_posiljka(id):
    try:
        with orm.db_session:
            posiljka = Posiljka[id]
            if posiljka:
                posiljka.delete()
                flash("Pošiljka je uspješno obrisana.", "success")
                return redirect(url_for('get_posiljke'))
            else:
                return make_response(jsonify({"error": "Posiljka not found"}), 404)
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )
       
@app.get("/posiljka/deliver")
def deliver_posiljka_form():
    broj_posiljke = request.args.get("broj_posiljke")
    return render_template("deliver_posiljka.html", broj_posiljke=broj_posiljke)

@app.post("/posiljka/deliver")
def deliver_posiljka():
    data = request.form.to_dict()
    try:
        with orm.db_session:
            posiljka = Posiljka.get(broj_posiljke=data["broj_posiljke"])
        
            if posiljka:
                if posiljka.status == "isporuceno":
                    flash("Pošiljka je već isporučena.", "error")
                    return render_template('deliver_posiljka.html')
                
                posiljka.status = "isporuceno"
                posiljka.datum_isporuke = datetime.datetime.now()
                flash("Pošiljka je uspješno isporučena.", "success")
                return render_template('deliver_posiljka.html')
            else:
                return make_response(jsonify({"error": "Posiljka not found"}), 404)
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )


@app.get("/grafovi")
def grafovi():
    try:
        with orm.db_session:
            posiljke = Posiljka.select()
            status_counts = {
                "poslano": 0,
                "isporuceno": 0,
                "neisporuceno": 0
            }
            for posiljka in posiljke:
                status_counts[posiljka.status] += 1

            # number of packages sent per day of the week
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            packages_per_day = {day: 0 for day in days_of_week}
            for posiljka in posiljke:
                day_of_week = posiljka.datum_slanja.strftime("%A")
                packages_per_day[day_of_week] += 1

            # number of packages per delivery time days
            delivery_time_days = {
                "0-1": 0,
                "2-3": 0,
                "4-5": 0,
                "6+": 0
            }
            for posiljka in posiljke:
                if posiljka.datum_isporuke:
                    delivery_time = (posiljka.datum_isporuke - posiljka.datum_slanja).days
                    if delivery_time <= 1:
                        delivery_time_days["0-1"] += 1
                    elif 2 <= delivery_time <= 3:
                        delivery_time_days["2-3"] += 1
                    elif 4 <= delivery_time <= 5:
                        delivery_time_days["4-5"] += 1
                    else:
                        delivery_time_days["6+"] += 1

            return render_template("grafovi.html", status_counts=status_counts, packages_per_day=packages_per_day, delivery_time_days=delivery_time_days)
            
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred", "details": str(e)}), 500
        )
    
@app.get("/seed")
def seed():
    try:
        with orm.db_session:    
            Posiljka.select().delete(bulk=True)

            addresses = [
                "Ilica 1", "Zagrebačka 2", "Vukovarska 3", "Savska 4", "Dubrovnik 5",
                "Split 6", "Rijeka 7", "Osijek 8", "Karlovac 9", "Pula 10"
            ]
            cities = [
                "Pula", "Rovinj", "Poreč", "Umag", "Labin", "Novigrad", "Buje", "Vodnjan", "Buzet", "Fažana",
                "Medulin", "Motovun", "Grožnjan", "Raša", "Vrsar", "Tar", "Savudrija", "Kaštelir", "Višnjan", "Žminj"
            ]
            names = ["Ivan", "Ana", "Marko", "Petra", "Luka", "Marija", "Josip", "Ivana", "Karlo", "Maja"]

            # Simplified random generation for seeding the database
            for i in range(1000):
                now = datetime.datetime.now()
                datum_slanja = now - datetime.timedelta(days=random.randint(1, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
                datum_isporuke = None



                if random.uniform(0, 1) < 0.9:
                    datum_isporuke = datum_slanja + datetime.timedelta(days=random.randint(1, 5), hours=random.randint(0, 23), minutes=random.randint(0, 59))

                if datum_isporuke != None and datum_isporuke <= now:
                    status = "isporuceno"
                elif datum_isporuke != None and datum_isporuke > now:
                    status = "neisporuceno"
                    datum_isporuke = None
                else:
                    status = random.choice(["poslano", "neisporuceno"])
                
                
                Posiljka(
                    adresa_prikupa=random.choice(addresses),
                    grad_prikupa=random.choice(cities),
                    adresa_dostave=random.choice(addresses),
                    grad_dostave=random.choice(cities),
                    naziv_posiljatelj=f"{random.choice(names)} Posiljatelj {i}",
                    tel_posiljatelj=f"+38512345{i:03}",
                    naziv_primatelj=f"{random.choice(names)} Primatelj {i}",
                    tel_primatelj=f"+38598765{i:03}",
                    status=status,
                    datum_slanja=datum_slanja,
                    datum_isporuke=datum_isporuke,
                    broj_posiljke=generate_broj_posiljke()
                )

            return render_template('seed.html')
    except Exception as e:
        return make_response(
            jsonify({"error": "An error occurred while seeding the database", "details": str(e)}), 500
        )
    
def generate_broj_posiljke():
    return uuid.uuid4().hex[:10].upper()

if __name__ == "__main__":
   app.run(port=5000, host='0.0.0.0', debug=True)
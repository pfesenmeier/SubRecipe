import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///subrecipe.db")

# I unilaterally decided this.
MAX_INGREDIENTS=12


@app.route("/")
@login_required
def index():
    """
    input: recipes1 database
    output: Russian-nesting doll structure of recipes

    input something like:
    ['name':'Rice Bowl';'children':'rice','sous vide egg', 'pickled red onion']
    """
    recipes = db.execute("SELECT * FROM recipes1")
    ingredients = db.execute("SELECT * FROM ingredients")

    for recipe in recipes:
        #children_id of NULL or [''] changed to empty list
        if recipe['children_id'] == None or recipe['children_id'] == '':
            recipe['children_id'] = []
        #children_id of comma seperated numbers changed to a list
        else:
            recipe['children_id'] = recipe['children_id'].split(',')
        #all recipes have empty list, used for completing tree
        recipe['children'] = []
        #all recipes incomplete, used for completing tree
        recipe['complete'] = False
        recipe['ingredients'] = []
        for ingredient in ingredients:
            if ingredient['recipe_id'] == recipe['recipe_id']:
                recipe['ingredients'].append(ingredient)


    while True:
        foundChild = False
        # get me first instance of child with
            # 1. no children of its own and
            # 2. who has not already been appended to their parents.
        for recipe in recipes:
            if not recipe['children_id'] and not recipe['complete']:
                child = int(recipe['recipe_id'])
                childRecipe = recipe
                recipe['complete'] = True
                foundChild = True
                break
        #if no child found, then tree is complete
        if foundChild == False:
            break
        #append found child recipe, etc. to all other recipes which it is a child
        for recipe in recipes:
            #iter over comma seperated list
            for children_id in recipe['children_id']:
                #if 'child ', the ID of the current recipe being found a home, is found in the list of child elements, children_id:
                if int(children_id) == child:
                    recipe['children'].append(childRecipe)
                    recipe['children_id'].remove(str(child))
    table = []
    #table = [{'name':'Rice Bowl', 'recipe_id:': 0, 'children':{'name':'pickled onions', 'children': {'name': 'vinegar', 'children':{'name':'perry','children':{'name':'sugar'}}}}}]

    #table for front end
    for recipe in recipes:
        if recipe['dish'] == 1:
            #could get rid of empty rows children_id, complete, and dish
            #just include name, children, recipe_id
            table.append(recipe)
    return render_template("index.html", table=table)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """
    takes in field for name, url, text
    """
    if request.method =="POST":
        if not request.form.get('recipe-name') and not request.form.get('old-recipe-name'):
            return apology("must provide name")
        if request.form.get('recipe-name') and request.form.get('old-recipe-name'):
            return apology("Must choose one name")
        name = request.form.get('recipe-name')
        old_name = request.form.get('old-recipe-name')
        if not request.form.get("parent") or request.form.get("parent") == '':
            return apology("must provide parent")
        parent = request.form.get('parent')
        if parent == 'newdish':
            dish = 1
        else:
            dish = 0
        #TODO: delete database, add checks for None, remove checks for '' fields
        #TODO: change texts to None if ''
        text = request.form.get('text')
        #TODO: change links to None if ''
        link = request.form.get('link')
        #if recipe is a new recipe
        if not old_name:
            db.execute("INSERT INTO recipes1 (name, dish, link, text) VALUES (:name, :dish, :link, :text);", name=name, dish=dish, link=link, text=text)
            child_id = db.execute("SELECT recipe_id FROM recipes1 ORDER BY recipe_id DESC LIMIT 1;")
            child_id= str(child_id[0]['recipe_id'])
        else:
            child_id = old_name
        if parent != 'newdish':
            #gets [{'children_id' = ''}] or [{'children_id' = NULL}] or [{'children_id' = 5,6}]
            children_id = db.execute("SELECT children_id FROM recipes1 WHERE recipe_id = :parent", parent=parent)
            #gets string, NULL, or ''
            children_id = children_id[0]['children_id']

            if children_id == '' or children_id == None:
            #TODO- change parent to recipe_id of recipe that you are adding
            #SELECT TOP 1 recipe_id FROM table ORDER BY recipe_id DESC;
                children_id = child_id
            else:
                children_id = children_id + ',' + child_id
            db.execute("UPDATE recipes1 SET children_id = :children_id WHERE recipe_id = :parent", children_id=children_id, parent=parent)

        #Add ingredients
        for i in range(MAX_INGREDIENTS):
            amount = request.form.get(f'amount{i}')
            unit = request.form.get(f'unit{i}')
            ingredient = request.form.get(f'ingredient{i}')
            if amount or unit or ingredient:
                db.execute("INSERT INTO ingredients (recipe_id, amount, unit, ingredient) VALUES (:recipe_id, :amount, :unit, :ingredient);", recipe_id=child_id, amount=amount, unit=unit, ingredient=ingredient)

        return redirect("/")


    else:
        parent_to_be = request.args.get("add-button")
        if parent_to_be:
            parent_to_be = db.execute("SELECT name, recipe_id FROM recipes1 WHERE recipe_id = :parent_to_be;", parent_to_be=parent_to_be)
            parent_to_be = parent_to_be[0]
        recipes = db.execute("SELECT name, recipe_id FROM recipes1 ORDER BY name")
        recipes.append({})
        recipes[-1]['name'] = 'New Dish'
        recipes[-1]['recipe_id'] = 'newdish'
        units = ["ea","g", "kg", "cup", "pint", "quart", "gal", "tsp", "Tbsp"]


        return render_template("add.html", recipes=recipes, units=units, max_ingredients = MAX_INGREDIENTS, parent_to_be=parent_to_be)

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username", "", str)
    if len(username) < 1 or db.execute("SELECT username FROM users WHERE username = :username", username=username):
        return jsonify(False)
    return jsonify(True)

@app.route("/delete", methods=["DELETE", "GET"])
@login_required
def delete():
    recipe_id = request.args.get('recipe_id')
    parent_id = request.args.get('parent_id')
    deletion = False
    if recipe_id and (int(parent_id) > 0):
        #gets [{'children_id' = ''}] or [{'children_id' = NULL}] or [{'children_id' = 5,6}]
        children_of_parent = db.execute("SELECT children_id FROM recipes1 WHERE recipe_id = :parent_id", parent_id=parent_id)
        #gets string, NULL, or ''
        children_of_parent = children_of_parent[0]['children_id']

        if len(children_of_parent) > 1:
                children_of_parent = children_of_parent.split(',')
        children_of_parent.remove(recipe_id)
        (",").join(children_of_parent)
        db.execute("UPDATE recipes1 SET children_id = :children_of_parent WHERE recipe_id = :parent_id", children_of_parent=children_of_parent, parent_id=parent_id)
        deletion = True
    elif recipe_id and (int(parent_id) < 0):
        db.execute("UPDATE recipes1 SET dish = 0 WHERE recipe_id = :recipe_id", recipe_id = recipe_id)
        deletion = True
    return jsonify(deletion=deletion)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/refill", methods=["GET"])
@login_required
def refill():
    recipe_id = request.args.get("recipe_id","",str)
    if recipe_id:
        recipe = db.execute("SELECT * FROM recipes1 WHERE recipe_id = :recipe_id", recipe_id=recipe_id);
        recipe = recipe[0]
        ingredients = db.execute("SELECT * FROM ingredients WHERE recipe_id = :recipe_id", recipe_id=recipe_id);
        return jsonify(recipe=recipe,
                       ingredients=ingredients,
                       max_ingredients=MAX_INGREDIENTS)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register user
    input: username, two copies of password: password and confirmation. all strings
    output: submission of user input via POST to /register and insert info into users.
    """
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Query database for username (checking duplicates)
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username does not already exist
        if len(rows) > 0:
            return apology("username not available", 400)

        # insert into registered into users
        pswdHash = generate_password_hash(request.form.get("password"))
        username = request.form.get("username")
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :pswdHash)", username=username, pswdHash=pswdHash)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/update", methods=["GET","POST"])
@login_required
def update():

    if request.method =="POST":
        # Update recipes table.
        if not request.form.get('old-recipe-name'):
            return apology("must provide name")
        recipe_id = request.form.get('old-recipe-name')
        text = request.form.get('text')
        link = request.form.get('link')
        db.execute("UPDATE recipes1 (text, link) VALUES (:text, :link) WHERE recipe_id=recipe_id;", text=text, link=link, recipe_id=recipe_id)

        # Update ingredients table.
        for i in range(MAX_INGREDIENTS):
            amount = request.form.get(f'amount{i}')
            unit = request.form.get(f'unit{i}')
            ingredient = request.form.get(f'ingredient{i}')
            if amount or unit or ingredient:
                db.execute("DELETE FROM ingredients WHERE recipe_id = :recipe_id", recipe_id=recipe_id)
                db.execute("INSERT INTO ingredients (recipe_id, amount, unit, ingredient) VALUES (:recipe_id, :amount, :unit, :ingredient);", recipe_id=recipe_id, amount=amount, unit=unit, ingredient=ingredient)

        return redirect("/")

    else:
        requested_recipe_id = request.args.get("update-button")
        if requested_recipe_id:
            # Get From Recipe Table
            requested_recipe = db.execute("SELECT * FROM recipes1 WHERE recipe_id = :requested_recipe_id;", requested_recipe_id=requested_recipe_id)
            requested_recipe = requested_recipe[0]
            # Get From Ingredients Table
            ingredients = db.execute("SELECT * FROM ingredients WHERE recipe_id = :requested_recipe_id;", requested_recipe_id=requested_recipe_id)
        else:
            requested_recipe=''
            ingredients=''
        recipes = db.execute("SELECT name, recipe_id FROM recipes1 ORDER BY name")
        recipes.append({})
        recipes[-1]['name'] = 'New Dish'
        recipes[-1]['recipe_id'] = 'newdish'
        units = ["ea","g", "kg", "cup", "pint", "quart", "gal", "tsp", "Tbsp"]
        return render_template("update.html", recipes=recipes, units=units, max_ingredients = MAX_INGREDIENTS, requested_recipe=requested_recipe, ingredients=ingredients, ingredientCount=len(ingredients))



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
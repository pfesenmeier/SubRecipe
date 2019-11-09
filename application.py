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

# Constants
MAX_INGREDIENTS = 12
UNITS = ["","cup", "tsp", "Tbsp", "pints", "quarts", "gallons", "grams", "kg", "lbs"]


@app.route("/")
@login_required
def index():
    """
    Recipes in SQL table record their children written down in the 'children_id' colunm.
    This script creates a dictionary structure where all entries are nested inside all their parents.
    """
    recipes = db.execute("SELECT * FROM recipes WHERE user_id = :user_id", user_id = session["user_id"])
    ingredients = db.execute("SELECT * FROM ingredients WHERE user_id = :user_id", user_id = session["user_id"])

    # Processing entries before sorting
    for recipe in recipes:
        # children_id of NULL or [''] changed to empty list.
        if recipe['children_id'] == None or recipe['children_id'] == '':
            recipe['children_id'] = []
        # children_id of comma seperated numbers changed to a list.
        else:
            recipe['children_id'] = recipe['children_id'].split(',')
        # All recipes have this empty list, where the children will go.
        recipe['children'] = []
        # All recipes labeled as incomplete before sorting.
        recipe['complete'] = False
        # Ingredients go here.
        recipe['ingredients'] = []
        # Here they go!
        for ingredient in ingredients:
            if ingredient['amount']:
                if float(ingredient['amount']).is_integer():
                    ingredient['amount'] = int(ingredient['amount'])
            if ingredient['recipe_id'] == recipe['recipe_id']:
                recipe['ingredients'].append(ingredient)

    # Sorting
    while True:
        foundChild = False
        for recipe in recipes:
            # Get me first instance of child with:
            # 1. No children of its own and
            # 2. Who has not already been appended to their parents.
            if not recipe['children_id'] and not recipe['complete']:
                child = int(recipe['recipe_id'])
                childRecipe = recipe
                recipe['complete'] = True
                foundChild = True
                break
        # Once you find a child:
        # 1. Append it to all its parents, and
        # 2. Remove its id from its parent.
        # Sorting will go until all children_id's are removed.
        if foundChild == False:
            break
        for recipe in recipes:
            for children_id in recipe['children_id']:
                if int(children_id) == child:
                    recipe['children'].append(childRecipe)
                    recipe['children_id'].remove(str(child))

    # Display the dishes on the front page.
    table = []
    for recipe in recipes:
        if recipe['dish'] == 1:
            table.append(recipe)
    table = sorted(table, key = lambda i: i['name'])
    return render_template("index.html", table=table)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """
    Add a recipe to another recipe.
    """

    if request.method =="POST":

        # Check inputs.
        if not request.form.get('recipe-name') and not request.form.get('old-recipe-name'):
            return apology("must provide name")
        if request.form.get('recipe-name') and request.form.get('old-recipe-name'):
            return apology("Must choose one name")
        if request.form.get('parent') == request.form.get('recipe-name') or request.form.get('parent') == request.form.get('old-recipe-name'):
            return apology("recipe cannot be own child")

        # Get inputs.
        parent = request.form.get('parent')
        name = request.form.get('recipe-name')
        old_name = request.form.get('old-recipe-name')
        text = request.form.get('text')
        link = request.form.get('link')
        if parent == 'newdish':
            dish = 1
        else:
            dish = 0

        # Write a row if recipe is new.
        if not old_name:
            db.execute("INSERT INTO recipes (name, dish, link, text, user_id) VALUES (:name, :dish, :link, :text, :user_id);", name=name, dish=dish, link=link, text=text, user_id = session["user_id"])
            recipe = db.execute("SELECT recipe_id FROM recipes WHERE user_id = :user_id ORDER BY recipe_id DESC LIMIT 1;", user_id=session["user_id"])
            recipe_id= str(recipe[0]['recipe_id'])
        # If an old recipe, check to make sure it is not a subrecipe of itself.
        # I cannot get this to work.
        else:
            recipe_id = old_name
            parent_ids = [{"recipe_id":str(parent)}]
                # select recipes where recipe_id is in children_id and user_id = user_id
            def checkLineage(parent_ids, recipe_id):
                for parent in parent_ids:
                    print(f"Parent id: {str(parent['recipe_id'])} Recipe_id: {recipe_id}")
                    if str(parent["recipe_id"]) == recipe_id:
                        return apology("recipe cannot be own child")
                    else:
                        child_list = db.execute("SELECT recipe_id FROM recipes WHERE user_id = :user_id AND (children_id = :parent OR children_id LIKE '%,' || :parent OR children_id LIKE '%,' || :parent || ',%');", parent=parent["recipe_id"], user_id=session["user_id"])
                        checkLineage(child_list, recipe_id)

            checkLineage(parent_ids, recipe_id)

        # Append the recipe's ID to the parent recipe.
        if parent:
            # Here you could get [{'children_id' = ''}] or [{'children_id' = NULL}] or [{'children_id' = 5,6}].
            children_id = db.execute("SELECT children_id FROM recipes WHERE recipe_id = :parent AND user_id = :user_id", parent=parent, user_id = session["user_id"])
            # Here you could get a string, NULL, or ''.
            children_id = children_id[0]['children_id']
            if children_id == '' or children_id == None:
                children_id = recipe_id
            else:
                children_id = children_id + ',' + recipe_id
            db.execute("UPDATE recipes SET children_id = :children_id WHERE recipe_id = :parent AND user_id = :user_id", children_id=children_id, parent=parent, user_id=session["user_id"])
        else:
            db.execute("UPDATE recipes SET dish = 1 WHERE recipe_id = :recipe_id AND user_id = :user_id", recipe_id=recipe_id, user_id=session["user_id"])

        # Add ingredients to ingredients table.
        for i in range(MAX_INGREDIENTS):
            amount = request.form.get(f'amount{i}')
            unit = request.form.get(f'unit{i}')
            ingredient = request.form.get(f'ingredient{i}')
            if ingredient:
                db.execute("INSERT INTO ingredients (recipe_id, amount, unit, ingredient, user_id) VALUES (:recipe_id, :amount, :unit, :ingredient, :user_id);", recipe_id=recipe_id, amount=amount, unit=unit, ingredient=ingredient, user_id=session["user_id"])

        return redirect("/")


    else:
        # Add buttons are at the bottom of every recipe on the homepage.
        # When user sent here this way, the recipe_id is displayed on the add page.
        parent_to_be = request.args.get("add-button")
        if parent_to_be:
            parent_to_be = db.execute("SELECT name, recipe_id FROM recipes WHERE recipe_id = :parent_to_be AND user_id = :user_id;", parent_to_be=parent_to_be, user_id = session["user_id"])
            parent_to_be = parent_to_be[0]


        recipes = db.execute("SELECT name, recipe_id FROM recipes WHERE user_id = :user_id ORDER BY name", user_id=session["user_id"])

        return render_template("add.html", recipes=recipes, units=UNITS, max_ingredients = MAX_INGREDIENTS, parent_to_be=parent_to_be)

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username", "", str)
    if len(username) < 1 or db.execute("SELECT username FROM users WHERE username = :username", username=username):
        return jsonify(False)
    return jsonify(True)

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        recipe_id = request.form.get("recipe-name")
        db.execute("DELETE FROM ingredients WHERE recipe_id = :recipe_id AND user_id = :user_id;", recipe_id=recipe_id, user_id=session["user_id"])
        db.execute("DELETE FROM recipes WHERE recipe_id = :recipe_id AND user_id = :user_id;", recipe_id=recipe_id, user_id=session["user_id"])
        return redirect("/")
    else:
        recipes = db.execute("SELECT name, recipe_id FROM recipes WHERE user_id = :user_id ORDER BY name", user_id = session["user_id"])
        return render_template("delete.html", recipes=recipes)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in. This route was written by the CS50 staff."""

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
    """Log user out. Route was written by CS50 staff."""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/refill", methods=["GET"])
@login_required
def refill():
    """Loads update page with ingredient information with JSON."""
    # Receives desired recipe ID.
    recipe_id = request.args.get("recipe_id","",str)
    if recipe_id:
        recipe = db.execute("SELECT * FROM recipes WHERE recipe_id = :recipe_id AND user_id=:user_id", recipe_id=recipe_id, user_id=session["user_id"])
        recipe = recipe[0]
        ingredients = db.execute("SELECT * FROM ingredients WHERE recipe_id = :recipe_id AND user_id = :user_id", recipe_id=recipe_id, user_id=session["user_id"])
        return jsonify(recipe=recipe,
                       ingredients=ingredients,
                       ingredientCount = len(ingredients))


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

@app.route("/remove", methods=["GET"])
@login_required
def remove():
    """
    Remove recipe from its parent and deletes its ingredients.
    Requests handled through AJAX, and authentication made here.
    """
    recipe_id = request.args.get('recipe_id')
    parent_id = request.args.get('parent_id')
    parent_id = int(parent_id)
    removed = False

    if recipe_id and (parent_id > 0):
        # Here could be [{'children_id' = ''}] or [{'children_id' = NULL}] or [{'children_id' = 5,6}].
        children_id = db.execute("SELECT children_id FROM recipes WHERE recipe_id = :parent_id AND user_id = :user_id", parent_id=parent_id, user_id=session["user_id"])
        # Here could be string, NULL, or ''.
        children_id = children_id[0]['children_id']

        if len(children_id) > 1:
                children_id = children_id.split(',')
        children_id.remove(recipe_id)
        children_id = (",").join(children_id)

        db.execute("UPDATE recipes SET children_id = :children_id WHERE recipe_id = :parent_id AND user_id = :user_id", children_id=children_id, parent_id=parent_id, user_id=session["user_id"])
        removed = True

    elif recipe_id and (int(parent_id) < 0):
        db.execute("UPDATE recipes SET dish = 0 WHERE recipe_id = :recipe_id AND user_id=:user_id", recipe_id=recipe_id, user_id=session["user_id"])
        removed = True
    return jsonify(removed=removed)

@app.route("/update", methods=["GET","POST"])
@login_required
def update():
    """Updates recipes."""

    if request.method =="POST":
        # Update recipes table.
        if not request.form.get('recipe-name'):
            return apology("must provide name")
        recipe_id = request.form.get('recipe-name')
        text = request.form.get('text')
        link = request.form.get('link')
        db.execute("UPDATE recipes SET text = :text, link = :link WHERE recipe_id = :recipe_id AND user_id = :user_id;", text=text, link=link, recipe_id=recipe_id, user_id=session["user_id"])

        # Update ingredients table.
        db.execute("DELETE FROM ingredients WHERE recipe_id = :recipe_id AND user_id = :user_id;", recipe_id=recipe_id, user_id=session["user_id"])
        for i in range(MAX_INGREDIENTS):
            amount = request.form.get(f'amount{i}')
            unit = request.form.get(f'unit{i}')
            ingredient = request.form.get(f'ingredient{i}')
            if amount or unit or ingredient:
                db.execute("INSERT INTO ingredients (recipe_id, amount, unit, ingredient, user_id) VALUES (:recipe_id, :amount, :unit, :ingredient, :user_id);", recipe_id=recipe_id, amount=amount, unit=unit, ingredient=ingredient, user_id=session["user_id"])

        return redirect("/")

    else:
        # Can recieve requests from each recipe.
        requested_recipe_id = request.args.get("update-button")
        if requested_recipe_id:
            # Get from recipe table.
            requested_recipe = db.execute("SELECT * FROM recipes WHERE recipe_id = :requested_recipe_id AND user_id=:user_id;", requested_recipe_id=requested_recipe_id, user_id=session["user_id"])
            requested_recipe = requested_recipe[0]
            # Get from ingredients table.
            ingredients = db.execute("SELECT * FROM ingredients WHERE recipe_id = :requested_recipe_id AND user_id=:user_id;", requested_recipe_id=requested_recipe_id, user_id=session["user_id"])
        else:
            requested_recipe={'recipe_id':'-1'}
            ingredients=''

        recipes = db.execute("SELECT name, recipe_id FROM recipes WHERE user_id = :user_id ORDER BY name", user_id = session["user_id"])

        return render_template("update.html", recipes=recipes, units=UNITS, max_ingredients = MAX_INGREDIENTS, requested_recipe=requested_recipe, ingredients=ingredients, ingredientCount=len(ingredients))



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
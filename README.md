Subrecipe allows users to collect all the recipes for a dish in one place.

To cook in a restaurant kitchen, a chef needs several recipes to execute a dish.
That means she will need dozens of recipes every season for her menus throughout the year.
With Subrecipe, she can easily access a list of her dishes and break them down into recipes and subrecipes.
The mobile-friendly app makes it easy to access the recipe you want in a fast-paced kitchen.

Components:
    application in python
        setup flask
    database in mysql
        users table
            id
            username
            passwordhash
        recipes table
            id
            title
            url
            text
            children
    static folder
        favicon.ico
        styles.css
    templates folder
        layout.html
            import Bootstrap
            include javascript for index.html
        login.html
            login screen.
        index.html
            Index page:
            	List of dishes.
            		Click on dishes, dropdown list of subrecipes.
            			Subrecipes when clicked
            			    show combination of text/link/subrecipes
            			    if nothing linked:
            			       no link
            			    if text and anything else:
            			        dropdown.
            			    if only link:
            				    link to the subrecipe (url/formatted text file)
            	            at end of all lists: 'Add dish/recipe/subrecipe' button -> link to add.html
        add.html
           form
                previous recipe -> select menu
                -or-
                title (required)
                url
                text
        error.html
            generic error page with messaging capabilities


Further functionality:
-add children from add screen
-index
-host somewhere on internet
-editing
-take and save photos
-preplist
-sharing
-cost-control functions. Pricing.
-volume to weight conversions via WolframAlpha
-search page


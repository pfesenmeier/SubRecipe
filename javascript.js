//if page just loaded, and no recipe requested,
    //
    //select 'nothing', and hide ingredient, text, and link fields.

//if page just loaded, and reciepe requested,
    //select all the elements form this element, show/hide ingredients, link and text
//if page being refilled, ask server for info, then hide fields

//page with 12 hidden ingredients, 1 hidden text, and 1 hidden link.
    //may or may not be filled with information

<script>
$(function(){
    var counter = 0;
    //var ingredientCount = JSON.parse({{ingredientCount|tojson|safe}});
    //var max_ingredients = JSON.parse({{max_ingredients|tojson|safe}});

    if (ingredientCount > 0){
        ShowIngredients(ingredientCount, max_ingredients);
        ShowAllButtonHelpTextLink();
    }

    $('#recipe-name').change(function(){
        var recipe_id = $(this).val();
        $.getJSON($SCRIPT_ROOT + '/refill', {
            recipe_id: `${recipe_id}`
        }, function(data){
            $('#text').text(data.recipe.text);
            $('#link').val(data.recipe.link);
            InsertIngredientInformation(ingredientCount, max_ingredients, data);
            ShowIngredients(ingredientCount, max_ingredients);
            ShowAllButtonHelpTextLink;
            counter = ingredientCounter;
        });
        ShowIngredients(ingredientCount, max_ingredients);
        ShowAllButtonHelpTextLink;
        counter = ingredientCounter;
        return false;
    });

    $('#show-entry-button').click(function(){
        $(`#ingredient-entry-${counter}`).show();
        counter += 1;
    });
});

function ShowAllButtonHelpTextLink(){
        $('#show-entry-button').show();
        $('#ingredienthelp').show();
        $('hide-until-request').show();
    }

function ShowIngredients(ingredientCount, max_ingredients){
    for (i = 0; i < ingredientCount; i++){
        $(`#ingredient-entry-${i}`).show();
    }
    for (j = ingredientCount; j < max_ingredients; j++){
        $(`#ingredient-entry-${j}`).hide();
    }
}

function InsertIngredientInformation(ingredientCount, max_ingredients, data){
    for (i = 0; i < ingredientCount; i++){
         $(`#amount${i}`).val(JSON.stringify(data.ingredients[i].amount));
         $(`#unit${i}`).val(JSON.stringify(data.ingredients[i].unit));
         $(`#ingredient${i}`).val(JSON.stringify(data.ingredients[i].ingredient));
    }
    for (j = ingredientCount; j < max_ingredients; j++){
        $(`#amount${j}`).val('');
        $(`#unit${j}`).val('');
        $(`#ingredient${j}`).val('');
    }
}
</script>

//begin old code
    <script>
        var ingredientCount = 0;
        var counter = 0;
        $(function(){
            $('#form-toggle').hide();

            $('#recipe-name').change(function(){
                var recipe_id = $(this).val();
                if (recipe_id > 0){
                $.getJSON($SCRIPT_ROOT + '/refill', {
                    recipe_id: `${recipe_id}`
                }, function(data){
                    var ingredientCounter = data.ingredients.length;
                    var max_ingredients = data.max_ingredients;
                    $('#text').text(data.recipe.text);
                    $('#link').val(data.recipe.link);
                    for (i = 0; i < ingredientCounter; i++){
                        $(`#amount${i}`).val(JSON.stringify(data.ingredients[i].amount));
                        $(`#unit${i}`).val(JSON.stringify(data.ingredients[i].unit));
                        $(`#ingredient${i}`).val(JSON.stringify(data.ingredients[i].ingredient));
                        $(`#ingredient-entry-${i}`).show();
                    }
                    for (j = ingredientCounter; j < max_ingredients; j++){
                        $(`#ingredient-entry-${j}`).hide();
                        $(`#amount${j}`).val('');
                        $(`#unit${j}`).val('');
                        $(`#ingredient${j}`).val('');
                    }
                    counter = ingredientCounter;
                });
                $('#form-toggle').show();
                return false;
                }
            });

             $('#show-entry-button').click(function(){
                $(`#ingredient-entry-${counter}`).show();
                counter += 1;
            });


            var requested_recipe = JSON.parse({{ requested_recipe.recipe_id | tojson  | safe}});
            if (typeof requested_recipe !== null){
                $('#recipe-name')
                    .val(requested_recipe)
                    .trigger('change');
            }

        });


    </script>
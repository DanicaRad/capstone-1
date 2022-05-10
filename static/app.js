const API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
const RANDOM_URL = 'https://api.spoonacular.com/recipes/random?apiKey=979dfa9f09634c8faf4ba8e387c1b0ab'
const BASE_URL = 'http://127.0.0.1:5000'

const ALERT = document.getElementById('js-alert')

// clear ALERT message and classes on page load/ refresh
document.addEventListener("DOMContentLoaded", clearAlertHtml);

// clear alert message classes from HTML 
function clearAlertHtml() {
    ALERT.innerText = "";
    ALERT.classList.remove("alert-success");
    ALERT.classList.remove("alert-danger");
    ALERT.classList.remove("alert-warning");
}

// ************ LIST FUNCTIONS ***********************************

// selects edit recipe/list form from recipes.html
recipeForm = document.querySelectorAll(".recipe-form")

// adds event listener to edit recipe/list forms 
recipeForm.forEach(recipe => {
    recipe.addEventListener("click", handleClick)
})

// handles edit list list click, sends post request, updates HTML if request successful
async function handleClick(e) {
    e.preventDefault();

    const data = e.target.dataset

    if(e.target.classList.contains('bi-heart-fill')) {
        const res = await sendPostRequest("recipes/favorite", data);
        if(res.status == 200) {
            e.target.classList.toggle('not-fav');
            e.target.classList.toggle('fav');
        }
    }

    if(e.target.tagName == 'LI') {
        const res = await sendPostRequest('recipes/add-to-list', data);
        if(res.status == 200) {
            showAlert(res);
            e.target.remove();
        }

    }

    if(e.target.id == 'trash') {

        const res = await sendPostRequest('lists/delete-from', data);
        if(res.status == 200) {
            showAlert(res);
            const recipe = document.getElementById(data.recipe)
            recipe.remove();
        }
    }
}

// post request function to edit list
async function sendPostRequest(endpoint, data) {
    const res = await axios({
        url:`${BASE_URL}/${endpoint}`,
        method: "POST",
        data: data
    })
    
    return res
}

// Selects delete list button from lists.html
const deleteListBtn = document.querySelectorAll(".delete-list")

// adds event listener to delete buttons
deleteListBtn.forEach(btn => {
    btn.addEventListener("click", deleteList)
})

// Sends request to delete user list from DB, deletes from HTML if successful
async function deleteList(e) {
    e.preventDefault();
    const data = e.target.dataset;

    if(e.target.tagName ==  'BUTTON') {

        const res = await sendPostRequest('lists/delete', data);

        if(res.status == 200) {
            showAlert(res);
            document.getElementById(data.id).remove();
        }
    }
}

// HTML manipulation ###############################

// renders response message in HTML alert 
async function showAlert(res) {
    ALERT.innerText = res.data.message;
    if(res.status != 200) {
        ALERT.classList.add('alert-danger');
    }
    ALERT.classList.add('alert-success');
    clearHTMLTimer();
}

// timer to remove HTML alert 
function clearHTMLTimer() {
    setTimeout(() => {
        clearAlertHtml();
    }, 3000);
}

// Test functions for querying API ##########################

async function getRecipe() {
    const res = await axios({
        url: `${RANDOM_URL}`,
        method: "GET",
        params: {"tags":"vegetarian,dessert","number":"1"}
    })

    const recipe = res.data.recipes[0]
    console.log(res)
    console.log(recipe)

}

async function searchRecipes() {
    const res = await axios({
        url: 'https://api.spoonacular.com/recipes/complexSearch?apiKey=979dfa9f09634c8faf4ba8e387c1b0ab',
        method: 'GET',
        params: {"query": "pasta",
                "number": "2",
                "addRecipeInformation": "true"}
    })

    console.log(res)
    console.log(res.data.results)
}

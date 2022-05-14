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
        if(res.status == 404) {
            showAlert(res);
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

// Get HTML element for conversion request event listener
const convertBtn = document.getElementById("ingredients")

if(convertBtn) {
    convertBtn.addEventListener("click", showConversions);
}

// Toggles HTML ingredient measures' visibility to show either US or Metric measures
async function showConversions(e) {
    e.preventDefault();

    if(e.target.tagName == "BUTTON") {
        const ingredients = document.querySelectorAll(".ingredient");
        ingredients.forEach(i => {
            i.classList.toggle("d-none");
        })

    }
}

// All public user lists functions #####################

// add event listener to show hidden recipes in public lists
// const showMore = document.getElementById("show-more");

// if(showMore) {
//     showMore.addEventListener("click", showHiddenRecipes);
// }

// get listCard from HTML
const listCard = document.querySelectorAll(".list-card")

// if listCard on page, add event lisener
if(listCard) {
    listCard.forEach(div => {
        div.addEventListener("click", showHiddenRecipes)
    })
}

// toggle hidden recipe visibility on click
function showHiddenRecipes(e) {

    if(e.target.id == "show-more") {
        const id = e.target.parentElement.id;
        const hiddenRecipes = document.getElementById(`hidden-recipes-${id}`);

        toggleRecipeVisibility(hiddenRecipes, e.target)
    }
}

function toggleRecipeVisibility(recipe, target) {
    recipe.classList.toggle("d-none");
    target.classList.toggle("bi-plus-lg");
    target.classList.toggle("bi-dash-lg");
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

async function recipeInfo(id) {
    try {
        const res = await axios({
        url: `https://api.spoonacular.com/recipes/${id}/information?apiKey=${API_KEY}`,
        method: "GET",
        params: {"includeNutrition":"false"}
        })
    } catch(e) {
        console.log("ERROR", e)
    }
}

async function similarRecipes(id) {
    const res = await axios({
        url: `https://api.spoonacular.com/recipes/${id}/similar?apiKey=${API_KEY}`,
        method: 'GET',
        params: {"number": "4"}
    })
    console.log(res);
    console.log("RES.DATA", res.data)
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

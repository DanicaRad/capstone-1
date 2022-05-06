const API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
const RANDOM_URL = 'https://api.spoonacular.com/recipes/random?apiKey=979dfa9f09634c8faf4ba8e387c1b0ab'
const BASE_URL = 'http://127.0.0.1:5000'

const ALERT = document.getElementsByClassName('alert')


async function getRecipe() {
    const res = await axios({
        url: `${RANDOM_URL}`,
        method: "GET",
        params: {"tags":"vegetarian,dessert","number":"1"}
    })

    const recipe = res.data.recipes[0]
    console.log(res)
    console.log(recipe)
    // const instructions = recipe.analyzedInstructions[0]
    // console.log(recipe.instructions)
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


// ************ LIST FUNCTIONS ***********************************

// Event listener to trigger adding to list
const listBtns = document.querySelectorAll('.lists-btn');

listBtns.forEach(btn => {
    btn.addEventListener("click", addRecipeToList)
})

// gets recipe and list ID's, sends POST request to add to list
async function addRecipeToList(e) {
    e.preventDefault();
    console.log("addRecipeToList - only adds recipe to list")
    if(e.target.tagName == 'A') {
        const res = await axios({
            url:`${BASE_URL}/recipes/add-to-list`,
            method: "POST",
            data: e.target.dataset
        })
        console.log(res);
        const message = res.data.message
    }
}

// Event listener for deleting recipe from list 
const deleteBtn = document.querySelectorAll(".delete-from-list")

deleteBtn.forEach(btn => {
    btn.addEventListener("click", deleteFromList)
})

/// gets Recipe and List IDs, sends post request to delete from list and deletes from HTML
async function deleteFromList(e) {
    e.preventDefault();

    if(e.target.tagName == 'SPAN') {

        const res = await axios({
            url: `${BASE_URL}/lists/delete-from`,
            method: 'POST',
            data: e.target.parentElement.dataset
        })

        if(res.status == 200) {
            console.log(res.data.message);
            console.log(e.target);

            const recipe = e.target.dataset.recipe;
            recipe.remove();
        }
    }
}

// const addRecipe = document.querySelectorAll(".add-recipe")

// addRecipe.forEach(recipe => {
//     recipe.addEventListener("click", getRequestData)
// })

// async function getRequestData(e) {
//     e.preventDefault();

//     console.log("getRequestData - adds to favs or list")
//     const data = e.target.dataset

//     if(e.target.tagName == 'SPAN') {
//         sendPostRequest("recipes/favorite", data);
//         e.target.classList.toggle('fav');
//     }

//     if(e.target.tagName == 'LI') {
//         sendPostRequest('recipes/add-to-list', data);
//     }
// }

async function sendPostRequest(endpoint, data) {
    const res = await axios({
        url:`${BASE_URL}/${endpoint}`,
        method: "POST",
        data: data
    })

    console.log("res in sendpost", res)
    console.log("res.status", res.status)
    return res
}

recipeForm = document.querySelectorAll(".recipe-form")

recipeForm.forEach(recipe => {
    recipe.addEventListener("click", handleClick)
})

async function handleClick(e) {
    e.preventDefault();

    const data = e.target.dataset

    if(e.target.id == 'heart') {
        const res = await sendPostRequest("recipes/favorite", data);
        if(res.status == 200) {
            console.log("HEART RES STATUS", res.status)
            e.target.classList.toggle('bi-heart');
            e.target.classList.toggle('bi-heart-fill');
        }
    }

    if(e.target.tagName == 'LI') {
        const res = await sendPostRequest('recipes/add-to-list', data);
        if(res.status == 200) {
            e.target.remove();
        }
    }

    if(e.target.id == 'trash') {

        console.log("data recipe", data.recipe)
        const res = await sendPostRequest('lists/delete-from', data);
        if(res.status == 200) {
            const recipe = document.getElementById(data.recipe)
            recipe.remove();
        }
    }
}
const API_KEY = '979dfa9f09634c8faf4ba8e387c1b0ab'
const BASE_URL = 'https://api.spoonacular.com/recipes/random?apiKey=979dfa9f09634c8faf4ba8e387c1b0ab'


async function getRecipe() {
    const res = await axios({
        url: `${BASE_URL}`,
        method: "GET",
        params: {"tags":"vegetarian,dessert","number":"1"}
    })

    const recipe = res.data.recipes[0]
    console.log(recipe)
    console.log(recipe.title)
    const instructions = recipe.analyzedInstructions[0]
    console.log(instructions.steps)
}

async function getRecipes() {
    const res = await axios({
        url: 'http://127.0.0.1:5000/recipes',
        method: "GET"
    })
    console.log(res)
}

async function searchRecipes() {
    const res = await axios({
        url: 'https://api.spoonacular.com/recipes/complexSearch?apiKey=979dfa9f09634c8faf4ba8e387c1b0ab',
        method: "GET",
        params: {"tags":"vegetarian,dessert","number":"3"}
    })

    console.log(res.data)
}
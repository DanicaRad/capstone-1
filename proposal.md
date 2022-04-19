# Spoontacular API meal planner - "Untitled Recipe Aggregator App"

### <font color="sky-blue">1. What goal will your website be designed to achieve?  </font>

Give food lovers and home chefs who value and invest in their health a single place to quickly and easily find, save and organize recipes that satisfy both their discerning culinary and dietary preferences. 

### <font color="sky-blue">2. What kind of users will visit your site? In other words, what is the demographic of your users?  </font>

The features of this site would most appeal to women already integrating tech in their daily lives, have both the time and financial resources to invest in food and their health but value time-saving conveniences. Women do 70-80% of shopping and meal preparation (according to a 2016 Bureau of Labor Statistics survey).  
- Location: US metropolitan, urban and suburban cities  
- Age: 25 - 55
- Gender: 70-80% female
- Education: Associate’s Degree or higher
- Familial status: Single, young and new parents, empty nesters
- Interests: Food, health, fitness, dietary trends, biohackers [sorry, so obnoxious]
- Occupation: white and pink collar, self-employed, stay-at-home parents  

### <font color="sky-blue">3. What data do you plan on using? You may have not picked your actual API yet, which is fine, just outline what kind of data you would like it to contain. </font>

I’m not really sure what this question is asking if it can be answered without knowing the API, but here’s my best guess:   

**Users:** 
- Username
- Email
- First, last name
- Age
- Dietary intolerances (API endpoints)
- Diet preferences (API endpoints)  

**Lists:** user created, named lists    
- Saved recipes (not sure what API recipe data I’ll save on app db)  

**From API, stored to user db:**  
- Recipe name, url, image, source
- Cuisine
- Servings
- Ready-in-minutes
- Dish type
- MAYBE Nutritional profile
- MAYBE Ingredients  

**From API for ui search:**
- All data from above saved to users db
- User search query terms
- Include/ exclude ingredients
- STRETCH: Recipe summary for search results  

### <font color="sky-blue">4. In brief, outline your approach to creating your project (knowing that you may not know everything in advance and that these details might change later). Answer questions like the ones below, but feel free to add more information:  </font>

- ### <font color="sky-blue">What does your database schema look like?  </font>

    **Users table:**  
    - All user registration data (e.g. username, password, email)
    - Foreign Key: list ids
    - Foreign key: diet id
    - Foreign key: intolerance id  

    **Diet table:** 
    - id
    - API endpoint diet name  

    **Intolerance table:** 
    - Id
    - API endpoint intolerance name  

    **List table/s:**
        Not sure how I’m going to design this yet in a way that makes getting user list data most “inexpensive.”  

- #### <font color="sky-blue">What kinds of issues might you run into with your API?  </font>

    ALL THE ISSUES! If I knew this, couldn’t I minimize running into them?
    - Website search parameters that are missing on API recipe data
    - Extracting data to save to website db
    - Recipe URL and image formats  

- ### <font color="sky-blue">Is there any sensitive information you need to secure?  </font>

    - API key
    - App secret key
    - User password
    - User email
    - User full name
    - User age, diet and intolerance profile (if preferred to be kept private by user)  

- ### <font color="sky-blue"> What functionality will your app include?  </font>

    - User register and login
    - Recipe search
    - Recipe save
    - Create lists and populate with recipes
    - Edit lists
    - MAYBE User recipe and list notes 
    - MAYBE share lists and recipes
    - MAYBE search public lists
    - MAYBE search and “follow” users  

- ### <font color="sky-blue">What will the user flow look like?  </font>

	**Rough start:**  
    - User starts on homepage with website and feature description; prompted to register or login
    - Once logged in/ registered, directed to their profile page  

    **Profile Page:**  
    - List of their lists
    - Click list to view recipes within lists
    - Click recipes within list to view recipes
    - Buttons to add recipes to or edit a list  

    **Search Recipes page:**  
    - Search query term text input 
    - Nutrition, diet, intolerances and cuisine filters
    - Some sort of sort-by feature  

- ### <font color="sky-blue">What features make your site more than CRUD? Do you have any stretch goals? </font> 

    The ability to create an account to save recipes to, organize by lists, share and search recipe lists make this site more than CRUD.  

    Stretch goals: “Suggested recipes” on user page, “similar recipes” on recipe pages, sort by “popular”, “Dinner Party/ Potluck” feature where users can share a recipe list with a group and group members can “claim” recipes to bring to party and other guests can see available recipes to claim. Similar to a gift registry.

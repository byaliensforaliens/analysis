import numpy as np
import pandas as pd
from functools import reduce
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn import linear_model

class Gapminder():
    # instantiating the class to carry out data wrangling
    def __init__(self,filename):
        self.df = pd.read_csv(filename)
        self.filename = filename.split("/")[-1].strip(".csv")
    
    # function was used initially to learn about the data and plan preprocessing
    def summary(self):
        print(self.columns.tolist())
        print("Shape of the dataframe is ",self.shape)
        print(self.isnull().sum())
        print("Maximum date in data is {}\n Minimum date is {}".format(self.year.max(),self.year.min()))
        print("---")
        if len(self.columns.tolist()) >= 4:
            print(self.describe())

    # this function carries out the heavy lifting shifting things around, dealing with missing values and changing data types
    def clean(self,imputer):
        self.df = self.df.T
        self.df.columns = self.df.iloc[0]
        self.df = self.df.iloc[1:,:]
        if imputer == False:
            self.df.dropna(axis=1,inplace=True)
        elif imputer == True:
            for i in self.df.columns.tolist():
                self.df[i].fillna((self.df[i].mean()), inplace=True)
        self.df = self.df.stack(0)
        self.df.index.set_names('year', level=len(self.df.index.names)-2,inplace=True)
        self.df = self.df.reset_index().rename(columns={0:f'{self.filename}'})
        self.df = self.df[(self.df['year'] >= '1990-01-01') & (self.df['year'] <= '2018-01-01')]
        num_cols = self.df.columns[-1:].tolist()
        for i in num_cols:
            self.df[i] = pd.to_numeric(self.df[i])
        return self.df

    # this function merges the individual dataframes into one dataset that can be used for analysis, visualisation and machine learning
    def merge(self,*args):
        args = list(args)
        self.df = reduce(lambda l,r: pd.merge(l,r,on=["year","country"]), args)
        self.df.columns = ["year","country","population","life_expectancy","income","hdi"]
        return self.df

class Visualisation():
    # instantiating the class to carry out EDA visualisation
    def __init__(self):
        self.df = pd.DataFrame()
    
    # function uses seaborn to plot correlation heatmap to explore variable relationship and regression plot for columns 
    def exploration(self,plot,x=None,y=None):
        sns.set_style("darkgrid")
        if plot == "regression":
            sns.regplot(x=x,y=y,data=self).set_title("Regression Plot")
            plt.show()
        elif plot == "heatmap":
            sns.heatmap(self.corr()).set_title("Correlation Heatmap")
            plt.show()
        elif plot == "box":
            sns.boxplot(x=self[x]).set_title("Box Plot of Variable")
            plt.show()
        elif plot == "corr":
            g = sns.pairplot(self)
            g.fig.suptitle("Correlation of variables")
            plt.show()

    def uni_variate(self):
        sns.distplot(self.income).set_title("Distribution Plot of Income")
        plt.show()
        sns.distplot(self.population).set_title("Count Plot of Population")
        plt.show()
        sns.countplot(self.life_expectancy).set_title("Count Plot of Life Expectancy")
        plt.show()

    # using an interactive scatter plot from the plotly library we can observe the behaviour of variables against life expectancy over time
    def animation(self,col,save):
        fig = px.scatter(self, x=col, y="life_expectancy", animation_frame="year", animation_group="country",
           size="population", color="country", hover_name="country", title="Change Over Time",
           log_x=True, size_max=55, range_x=[100,100000], range_y=[25,90])
        if save == True:
            fig.write_html(f"./visualisations/{col}_vs_life_expectancy.html")
            fig.show()
        else:
            fig.show()
        

class MachineLearning():
    # instantiating machine learning class to carry out predictions on life expectancy based on independent variables
    def __init__(self):
        self.df = pd.DataFrame()

    # function encodes the country column and gives it dummy variables to be processed by the regression algorithm
    def encoding(self):
        self = self[["year","country","population","income","hdi","life_expectancy"]]
        self["year"] = pd.to_datetime(self["year"])
        self["year"] = self["year"].dt.year
        cols = list(self.select_dtypes(include=['category','object']))
        le = LabelEncoder()
        for feature in cols:
            try:
                self[feature] = le.fit_transform(self[feature])
            except:
                print('Error encoding '+feature)
        return self
   
    # splits the dataset into training and testing sets and stacks together two linear regression models to generate coefficients and accuracy scores
    def run(self):
        X = self[self.columns[:-1]]
        y = self[self.columns[-1]]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
        reg = linear_model.BayesianRidge()
        reg.fit(X_train,y_train)
        y_pred = reg.predict(X_test)
        reg2 = linear_model.LinearRegression()
        reg2.fit(X_train,y_train)
        y_pred2 = reg2.predict(X_test)
        cdf = pd.DataFrame(reg.coef_, X.columns, columns=['Coefficients'])
        print(f"""{cdf}\n
        Regression coefficients represent the mean change in the response variable
        for one unit of change in the predictor variable
        while holding other predictors in the model constant.\n""")
        print(f"Accuracy score for a Bayseian model is {reg.score(X_test, y_test):.5f}, for a Linear model is {reg2.score(X_test, y_test):.5f}")

def conclusion():
    print(""" It can be concluded that money does, to an extent buy a longer life as we witness a positive correlation between the two factors over time.
    Another interesting effect was that of population, which showed that the data collection process contained many outliers through our visualisation of a box plot.
    We could use more features either through engineering or bringing in more data via the ETL pipeline we have built for this project.
    It could also be interesting to run a KMeans Clustering algorithm on the dataset to group countries into separate categories
    of life expectancy metrics.""")
    
# bulk of work carried out in this function to bring everything together
def main():
    population = Gapminder("./gapminder_data/population_total.csv").clean(imputer=False)
    life_expectancy = Gapminder("./gapminder_data/life_expectancy_years.csv").clean(imputer=False)
    income = Gapminder("./gapminder_data/income_per_person_gdppercapita_ppp_inflation_adjusted.csv").clean(imputer=False)
    human_development = Gapminder("./gapminder_data/hdi_human_development_index.csv").clean(imputer=True)
    data = pd.DataFrame()
    data = Gapminder.merge(data,population,life_expectancy, income, human_development)
    print("Analysing population data...")
    Gapminder.summary(population)
    print("Analysing life expectancy data...")
    Gapminder.summary(life_expectancy)
    print("Analysing income data...")
    Gapminder.summary(income)
    print("Analysing HDI dataset...")
    Gapminder.summary(human_development)
    print("Analysing complete data...")
    Gapminder.summary(data)
    print("QUESTION - HOW DO THE VARIABLES CORRELATE WITH EACH OTHER?")
    print("Assessing correlation of variables using correlation heatmap...")   
    Visualisation.exploration(data,plot="heatmap")
    print("Assessing correlation of income against life expectancy using regression plot...")
    Visualisation.exploration(data,plot="regression",x="income",y="life_expectancy")
    print("Assessing correlation of variables against each other using pair plots...")
    Visualisation.exploration(data,plot="corr")
    print("Asessing summary statistics on population variable using box plot...")
    Visualisation.exploration(data,plot="box",x="population")
    print("QUESTION - DOES INCOME BUY A LONGER LIFE?")
    print("Animating change in life expectancy against income over time...")
    Visualisation.animation(data,"income",save=False)
    print("Running prediction algorithm and stats...")
    df = MachineLearning.encoding(data)
    MachineLearning.run(df)
    print("Printing conclusion...\n")
    conclusion()
    
# runs program
if __name__ == '__main__':
    main()
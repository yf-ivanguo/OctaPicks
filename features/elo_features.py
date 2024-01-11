import math

class Elo():
    def __init__(self):
        self.TAU = 0.5
        self.EPSILON = 0.000001
        self.GLICKO_SCALE_FACTOR = 400 / math.log(10)
        self.WIN = 1
        self.LOSS = 0
        self.RATING_INIT = 1500
        self.RD_INIT = 350
        self.VOL_INIT = 0.06

    """
    Public Function
    """
    def compute_elo(self, df):
        target_df = df

        # Compute Glicko ratings for every match
        for index, row in target_df.iterrows():
            fighter_a_updated_rating, fighter_a_updated_rd, fighter_a_updated_vol = self.__compute_elo_ratings(df, row['fighter_a_id'], index)
            fighter_b_updated_rating, fighter_b_updated_rd, fighter_b_updated_vol = self.__compute_elo_ratings(df, row['fighter_b_id'], index)

            df.at[index, 'fighter_a_elo_rating'] = fighter_a_updated_rating
            df.at[index, 'fighter_a_elo_rd'] = fighter_a_updated_rd
            df.at[index, 'fighter_a_elo_vol'] = fighter_a_updated_vol
            df.at[index, 'fighter_b_elo_rating'] = fighter_b_updated_rating
            df.at[index, 'fighter_b_elo_rd'] = fighter_b_updated_rd
            df.at[index, 'fighter_b_elo_vol'] = fighter_b_updated_vol
        
        return df

    """
    Private Functions
    """

    def __compute_elo_ratings(self, df, p_id, index):
        # Find all the previous fights
        all_prev_games = df.iloc[:index]

        # If there have been fights before this fight ->
        if not all_prev_games.empty:

            # Get the ID values of fighter 1 and fighter 2
            fighter_a_id_vals = all_prev_games.fighter_a_id.values
            fighter_b_id_vals = all_prev_games.fighter_b_id.values

            # Get the fights where fighter 1 and fighter 2 have fought
            prev_games = all_prev_games[((fighter_a_id_vals == p_id) | (fighter_b_id_vals == p_id))]

            # Set default initial Glicko2 elo
            player_elo_rating = self.RATING_INIT
            player_elo_rd = self.RD_INIT
            player_elo_vol = self.VOL_INIT

            # If the fighters have fought prior ->
            if not prev_games.empty:

                # Find the result of the last fight
                last_game = prev_games.iloc[-1]
                res = self.WIN if p_id == last_game['winner_id'] else self.LOSS

                # Set fighter and opponent variables accordingly
                if p_id == last_game['fighter_a_id']:
                    player = "fighter_a"
                    opp = "fighter_b"
                else:
                    player = "fighter_b"
                    opp = "fighter_a"

                # Get the Glicko2 elo prior to the last fight
                player_rating = last_game[f'{player}_elo_rating']
                player_rd = last_game[f'{player}_elo_rd']
                player_vol = last_game[f'{player}_elo_vol']
                opp_rating = last_game[f'{opp}_elo_rating']
                opp_rd = last_game[f'{opp}_elo_rd']

                # Update the rating based on previous match results
                updated_rating, updated_rd, updated_vol = self.__get_updated_rating(player_rating, player_rd, player_vol, opp_rating, opp_rd, res)

                player_elo_rating = updated_rating
                player_elo_rd = updated_rd
                player_elo_vol = updated_vol

            return player_elo_rating, player_elo_rd, player_elo_vol
        return self.RATING_INIT, self.RD_INIT, self.VOL_INIT

    def __get_updated_rating(self, player_rating, player_rd, player_vol, opp_rating, opp_rd, res):
        player_elo_rating = (player_rating - self.RATING_INIT) / self.GLICKO_SCALE_FACTOR
        player_elo_rd = player_rd / self.GLICKO_SCALE_FACTOR
        opp_elo_rating = (opp_rating - 1500) / self.GLICKO_SCALE_FACTOR
        opp_elo_rd = opp_rd / self.GLICKO_SCALE_FACTOR

        e_val = self.__E(player_elo_rating, opp_elo_rating, opp_elo_rd)
        g_val = self.__g(opp_elo_rd)
        v_val = self.__v(e_val, g_val)
        delta_val = self.__delta(v_val, opp_elo_rd, res, e_val)
        elo_volPrime = self.__volPrime(player_elo_rd, player_vol, v_val, delta_val)
        elo_rdPrime = self.__rdPrime(player_elo_rd, v_val, elo_volPrime)
        elo_ratingPrime = self.__ratingPrime(player_elo_rating, elo_rdPrime, g_val, res, e_val)
        
        player_new_vol = elo_volPrime
        player_new_rd = self.GLICKO_SCALE_FACTOR * elo_rdPrime
        player_new_rating = self.GLICKO_SCALE_FACTOR * elo_ratingPrime + 1500
        return player_new_rating, player_new_rd, player_new_vol

    # Rating functions
    def __v(self, e_val, g_val):
        return ((g_val ** 2 * e_val) * (1 - e_val)) ** -1

    def __g(self, elo_rd):
        return 1 / math.sqrt(1 + (3 * elo_rd ** 2 / math.pi ** 2))

    def __E(self, player_elo_rating, opp_elo_rating, opp_elo_rd):
        return 1 / (1 + math.exp(- self.__g(opp_elo_rd) * (player_elo_rating - opp_elo_rating)))

    def __delta(self, v_val, score, e_val, g_val):
        return v_val * g_val * (score - e_val)

    def __volPrime(self, elo_rd, vol, v_val, delta_val):
        a = math.log(vol ** 2)
        A = a
        B = 0

        if delta_val ** 2 > (elo_rd ** 2 + v_val):
            B = math.log(delta_val ** 2 - elo_rd ** 2 - v_val)
        else:
            k = 1
            while self.__function(a - k * math.sqrt(self.TAU ** 2), elo_rd, v_val, delta_val, a) < 0:
                k += 1
            B = a - k * self.TAU

        fnA = self.__function(A, elo_rd, v_val, delta_val, a)
        fnB = self.__function(B, elo_rd, v_val, delta_val, a)

        while abs(B - A) > self.EPSILON:
            C = A + (A - B) * fnA / (fnB - fnA)
            fnC = self.__function(C, elo_rd, v_val, delta_val, a)
            if fnC * fnB < 0:
                A = B
                fnA = fnB
            else:
                fnA /= 2
            B = C
            fnB = fnC

        if abs(B - A) <= self.EPSILON:
            return math.exp(A / 2)
        else:
            raise ArithmeticError()

    def __function(self, x, rd, v, delta, a):
        return (math.exp(x) * (delta ** 2 - rd ** 2 - v - math.exp(x))) / (2 * (rd ** 2 + v + math.exp(x)) ** 2) - (x - a) / self.TAU ** 2

    def __rdPrime(self, rd, v, volPrime):
        rdStar = math.sqrt(rd ** 2 + volPrime ** 2)
        return 1 / math.sqrt(1 / rdStar ** 2 + 1 / v)

    def __ratingPrime(self, rating, rdPrime, g, score, E):
        return rating + rdPrime ** 2 * g * (score - E)
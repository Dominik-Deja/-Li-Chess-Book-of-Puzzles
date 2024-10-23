import pandas as pd
import yaml
import chess

def load_puzzles(path=None):
    return pd.read_table(path, compression='zstd', header=0, sep=',')

def filter_puzzles(data, themes=None, all_themes=True, min_rating=None, max_rating=None, n=None):
    """Filter puzzles based on themes and rating range."""
    # Convert Rating column to numeric
    data["Rating"] = pd.to_numeric(data["Rating"], errors='coerce')
    # Filter by rating range
    if min_rating:
        data = data[data["Rating"] >= min_rating]
    if max_rating:
        data = data[data["Rating"] <= max_rating]
    # Filter by themes
    if themes:
        # Initialize the filter mask to select all rows initially
        filter_mask = pd.Series(True, index=data.index)
        if all_themes:
            for theme in themes.split(' '):
                # Update the filter mask to only select rows where the theme is present
                filter_mask &= data["Themes"].str.contains(theme, na=False)
        else:
            for theme in themes.split(' '):
                # Update the filter mask to select rows where at least one theme is present
                filter_mask |= data["Themes"].str.contains(theme, na=False)
        # Apply the final filter
        data = data[filter_mask]
    # Apply next move to FEN and get moves from the second move onwards
    for idx, row in data.iterrows():
        moves = row['Moves'].split()
        if len(moves) >= 2:
            board = chess.Board(row['FEN'])
            board.push(chess.Move.from_uci(moves[0]))
            data.at[idx, 'FEN'] = board.fen()
            data.at[idx, 'Moves'] = ' '.join(moves[1:])
        else:
            print(f"Skipping row {idx + 1}: Insufficient moves")
    if data.shape[0] <= n:
        return data
    else:
        return data.iloc[:n, :]

def translate_moves(moves, fen):
    board = chess.Board(fen)
    proper_moves = []
    for move in moves.split(" "):
        chess_move = chess.Move.from_uci(move)
        algebraic_move = board.san(chess_move)
        proper_moves.append(algebraic_move)
        board.push(chess_move)
    return " ".join(proper_moves)

def black_or_white(fen, answer=True):
    if answer:
        return f"\\whitecircle" if chess.Board(fen).turn else f"\\blackcircle"
    else:
        return f"" if chess.Board(fen).turn else f"... "

def generate_text(puzzles, themes, n, min_rating, max_rating):
    text = f"""
\\documentclass{{article}}
\\usepackage{{skak}}
\\usepackage{{graphicx}}
\\usepackage[margin=1.5cm, a4paper]{{geometry}}
\\usepackage{{multicol}}
\\usepackage{{tikz}}

% Define the scaling factor
\\newcommand{{\\chessScaleFactor}}{{0.7}}
\\newcommand{{\\NumberDiagramSpace}}{{\\vspace{{0.2cm}}}}
\\newcommand{{\\whitecircle}}{{\\tikz\\draw[black,fill=white] (0,0) circle (3pt);}}
\\newcommand{{\\blackcircle}}{{\\tikz\\draw[black,fill=black] (0,0) circle (3pt);}}

\\begin{{document}}

{{\\centering \\section*{{The Lichess Book of {n} Puzzles covering {themes} theme(s) from {min_rating} to {max_rating}}}}}

\\vspace{{1cm}}
    """

    for i, (_, row) in enumerate(puzzles.iterrows(), 1):
        if i % 2 == 1:
            text += f"""
\\noindent
\\parbox[t]{{0.48\\textwidth}}{{%
\\centering
\\textbf{{\\#{i}}} {black_or_white(row.FEN)}\\\\
\\NumberDiagramSpace
\\resizebox{{\\chessScaleFactor\\linewidth}}{{!}}{{%
\\newgame
\\fenboard{{{row['FEN']}}}
\\showboard
}}
}}\\hfill
            """
        else:
            text += f"""\\parbox[t]{{0.48\\textwidth}}{{%
\\centering
\\textbf{{\\#{i}}} {black_or_white(row.FEN)}\\\\
\\NumberDiagramSpace
\\resizebox{{\\chessScaleFactor\\linewidth}}{{!}}{{%
\\newgame
\\fenboard{{{row['FEN']}}}
\\showboard
}}
}}
            """
        if i % 6 == 0:
            text += f"""
\\vspace{{1cm}}
\\newpage
            """
        elif i % 2 == 0:
            text += f"""
\\vfill
            """

    text += f"""\\newpage
\\begin{{multicols}}{{2}}
    """
    for i, (_, row) in enumerate(puzzles.iterrows(), 1):
        text += f"""\\textbf{{\\#{i}}} {black_or_white(row.FEN, answer=False)}{translate_moves(row.Moves, row.FEN)}\\\\


        """
    text += f"""\\end{{multicols}}
\\end{{document}}
    """
    return text



def main():
    # Load config file
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    min_rating = config.get("min_rating")
    max_rating = config.get("max_rating")
    themes = config.get("themes")
    all_themes = config.get("all_themes")
    n = config.get("n")
    # Load data
    puzzles = load_puzzles('data/lichess_db_puzzle.csv.zst')
    print(puzzles.shape)
    # Filter puzzles
    filtered_puzzles = filter_puzzles(puzzles, themes=themes, all_themes=all_themes, min_rating=min_rating, max_rating=max_rating, n=n)
    print(filtered_puzzles.shape)
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(generate_text(filtered_puzzles, themes, min_rating, max_rating, n))

if __name__ == "__main__":
    main()

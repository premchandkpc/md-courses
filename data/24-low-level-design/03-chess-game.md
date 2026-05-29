# Chess Game — Low Level Design

Design a two-player chess game with complete move validation, game state management, and check/checkmate detection.

## Requirements

### Functional
1. Two players take turns making moves (White goes first)
2. All standard chess rules enforced: piece movement, capture, castling, en passant, pawn promotion
3. Detect check, checkmate, stalemate, draw by insufficient material
4. Track captured pieces, move history
5. Validate moves before executing
6. Support undo/redo of moves
7. Provide score/draw detection

### Non-Functional
1. Move validation < 10ms
2. Support for online play (networking optional)
3. Persist game state for resume

## Class Design

### Piece Hierarchy
```
Piece (abstract)
├── King      — moves 1 square any direction; castling
├── Queen     — moves any direction, any distance
├── Rook      — horizontal/vertical; castling partner
├── Bishop    — diagonal
├── Knight    — L-shape (2+1); jumps over pieces
└── Pawn      — 1 forward (2 from start); diagonal capture; en passant; promotion
```

### Core Classes

```java
enum Color { WHITE, BLACK }
enum PieceType { KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN }

abstract class Piece {
    Color color;
    Position position;
    boolean hasMoved;  // for castling, pawn double-move
    abstract List<Move> getValidMoves(Board board);
    abstract PieceType getType();
}

class Board {
    Piece[][] squares;          // 8x8 grid
    List<Piece> capturedWhite;
    List<Piece> capturedBlack;
    Map<Color, Position> kingPositions;

    Piece getPiece(Position pos);
    void setPiece(Position pos, Piece piece);
    boolean isInBounds(Position pos);
    boolean isPathClear(Position from, Position to);  // for sliding pieces
}

class Move {
    Position from;
    Position to;
    Piece movedPiece;
    Piece capturedPiece;
    boolean isCastling;
    boolean isEnPassant;
    boolean isPromotion;
    PieceType promotionType;   // QUEEN by default
}

class Game {
    Board board;
    Color currentTurn;
    List<Move> moveHistory;
    GameStatus status;  // ACTIVE, CHECK, CHECKMATE, STALEMATE, DRAW

    boolean makeMove(Position from, Position to);
    boolean isValidMove(Position from, Position to);
    void undoMove();
    List<Position> getValidMoves(Position pos);
    boolean isInCheck(Color color);
    boolean isCheckmate(Color color);
    boolean isStalemate(Color color);
}
```

## Movement Rules

| Piece | Movement | Special |
|-------|----------|---------|
| King | 1 square any direction | Castling: king + rook move together |
| Queen | Any direction, any distance | — |
| Rook | Horizontal/vertical, any distance | Used in castling |
| Bishop | Diagonal, any distance | — |
| Knight | 2+1 L-shape | Jumps over pieces |
| Pawn | 1 forward (2 from start) | Diagonal capture; en passant; promotion on rank 8/1 |

## Move Validation Flow

```
1. Is source position occupied by current player's piece?
2. Is destination valid for this piece type (basic movement)?
3. Is path clear? (for sliding pieces: rook, bishop, queen)
4. Does this leave own king in check?
5. Special cases: castling eligibility, en passant, pawn promotion
```

## Check/Checkmate Detection

```
isInCheck(color):
  1. Find king position
  2. Check if any opponent piece can reach it

isCheckmate(color):
  1. Is current player in check?
  2. Can any piece of current player make a legal move?
     - If no legal moves + in check = checkmate
     - If no legal moves + not in check = stalemate
```

## Enums & Constants

```java
enum GameStatus {
    ACTIVE, WHITE_WIN, BLACK_WIN, STALEMATE, DRAW
}

class Constants {
    static final int BOARD_SIZE = 8;
    static final int MAX_MOVES_WITHOUT_CAPTURE = 50;  // 50-move rule
}
```

## Design Patterns Used

| Pattern | Application |
|---------|-------------|
| **Strategy** | Different move validation algorithms per piece type |
| **Factory** | Create pieces by type (PieceFactory) |
| **Command** | Encapsulate moves for undo/redo |
| **Observer** | Notify UI of game state changes |
| **State** | Game states (ACTIVE, CHECK, CHECKMATE, etc.) |

## Learning Path

1. Implement Board class with 8x8 grid
2. Implement each piece's movement validation
3. Add check/checkmate detection
4. Add special moves: castling, en passant, promotion
5. Add undo/redo, game history
6. Add AI opponent (minimax with alpha-beta pruning)

## Visualizations

- [Interactive Chess Board](chess-board-viz.html) — playable chess with valid move highlighting, piece hierarchy diagram, and move log

**Next**: [Splitwise Design](04-splitwise.md) · [File System Design](05-file-system.md)

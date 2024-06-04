# 🕹️whynes
<img src="https://github.com/thomascrha/whynes/blob/main/whynes.png?raw=true" align="middle" width="250" height="250">

__A Nintendo Entertainment System emulator written in python.__

__(pssst... it's not finished yet)__

## Why ?


Why not. This is a project designed as an educational experiment so I can do two things:

* learn how to emulate hardware in software.
* use that knowledge to then learn other languages.

I know python pretty well - I've been using it professionally for (insert flex) years and a I'm pretty comfortable with
it (no error; good program).

I've always wanted to learn how to write an emulator, but I don't know other more suitable languages to do that in - so
I thought why not just write one in python. Is writing a emulator in python a good idea ? No.

Then I can implement the same emulator in other languages and *bing bong boom* I've become a
`giga-polyglot-chad programmer`.

## Rules

1. When Mario can jump, I've finished.

## Snake (Bonus)

I needed a way to confirm my implementation of the CPU was correct, so I found a [snake game](https://gist.github.com/wkjagt/9043907)
written in 6502 assembly and given the instructions [here](https://bugzmanov.github.io/nes_ebook/chapter_3_4.html), I
implemented a snake game using PyGame (SDL) and pyinput for controls and the CPU implementation.

```console
pip install .[dev]  # install all the dependencies including dev P.S. on zsh surround '.[dev]' quotes
python3 src/snake.py
```

<img src="https://github.com/thomascrha/whynes/blob/main/snake-boi.gif?raw=true" align="centre">

## Resources

[Nesdev Wiki](http://wiki.nesdev.com/w/index.php/Nesdev_Wiki)

[Online Assembler/Dissembler](https://skilldrick.github.io/easy6502/)

[Instruction Set Manual](https://www.pagetable.com/c64ref/6502/?tab=2)

[Writing NES Emulator in Rust](https://bugzmanov.github.io/nes_ebook/chapter_1.html)

## Related Memes
<img src="https://media.tenor.com/KA4TdkOcYT8AAAAM/jeff-goldblum.gif" width="70%">

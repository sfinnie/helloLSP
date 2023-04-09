// Grammar for the "greet" demonstration language

module.exports = grammar({
  name: 'greet',

  rules: {
    // TODO: add the actual grammar rules
    source_file: $ => repeat($.greeting),

    greeting: $ => seq(
      field('salutation', $._salutation),
      field('name', $.name)
    ),

    _salutation: $ => choice(
      $.hello,
      $.goodbye
    ),

    hello: $ => /[Hh]ello/,
    goodbye: $ => /[Gg]oodbye/,
    
    name: $ => /[A-Za-z]+/
  }
});


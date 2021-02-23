class Token:
    class TokenException(Exception) :
        pass 

    defined_tokens = ['Paper','Link','PMID','DOI',
                'Date','Note','desc',
                'Journal', 'Volume', 'Issue', 'Pages',
                'Contributor', 'Association', 'Contact', 'Fax', 'Email',
                'Keyword',
                'Species','Reef','Loc','Coord','ID',
                'Location','City','Country',
                'Method','XREF',
                'Software','Version',
                'Instrument',
                'Data','Repo-Type','Size']
    # Note: Spellchecking stuff we were thinking about earlier?

    # Called multiple times, not only when tokens are created from a file.
    def __init__(self, level, prev, major, other, body, line) :
        self.level = level
        self.prev_tokens = prev
        self.major_token = major
        self.other_tokens = other
        self.body = body
        self.lineno = line
    
    # The only time a token is created from the file.
    # If you want to do something on *initial token creation*, do it here.
    @classmethod
    def fromLine(cls, str_inp, lineno) :
        str_inp = str_inp.strip()
        token, body = str.split(str_inp,' ', 1)
        token = str.replace(token, '@', '')
        tokens = token.split('-') # See how many tokens we get out of this
        level = len(tokens)

        main_token = tokens[0]
        if main_token not in Token.defined_tokens :
            print("Warning: Unknown token " + main_token + " found on line " + str(lineno))

        return cls(level, [], main_token, tokens[1:], body, lineno)

    # Given a file location, generates all of the tokens in the file.
    @staticmethod
    def generate_tokens(fileloc) :
        tokens = []
        with open(fileloc, 'r') as f:
            all_lines = f.readlines()
            for i, line in enumerate(all_lines) :
                # TODO : If we want fields to be able to go over multiple lines,
                #        need to add the logic here.
                if(line.strip() != "" and line[0] == '@') :
                    tokens.append(Token.fromLine(line, i))
        return tokens
    
    # Returns only tokens that are 'top-level' (are not sub-tokens.)
    # This is not necessarily tokens that are top level of the paper, as we may
    #   have 'reveal'ed already, entering a token block (such as a Paper block.)
    @staticmethod
    def get_major_tokens(tokens) :
        only_toplevel = Token._get_top_level(tokens)
        return(list(map(lambda x: x.major_token, only_toplevel)))
    
    # Given a lsit of tokens, return the indices of major tokens (as the range
    #   between two major tokens should contain all sub-tokens of the first major
    #   token.)
    @staticmethod
    def get_token_blocks(tokens) :
        indices = []
        for i, token in enumerate(tokens) :
            if token.level == 1:
                indices.append(i)
        return(indices)

    # Private
    @staticmethod
    def _get_top_level(tokens) :
        return(list(filter(lambda x: x.level == 1, tokens)))

    @staticmethod
    def reveal_several(tokens) :
        revealed = []
        for token in tokens :
            revealed.append(token.reveal())
        return(revealed)

    def clone(self) :
        return(Token(self.level, self.prev_tokens, self.major_token, self.other_tokens, self.body, self.lineno))

    def reveal(self) :
        # Move down 1 level of tokens
        newToken = self.clone()
        return(newToken._reveal())
    
    def get_major(self) :
        return(self.major_token)

    def get_body(self) :
        return(self.body)
    
    def get_line(self) :
        return(self.lineno)

    # Private
    # Don't want people calling this because it modifies the internals of a token. We want them to use the above method
    #   which first makes a copy of the current token, to prevent data loss.
    def _reveal(self) :
        self.level = self.level - 1
        self.prev_tokens.append(self.major_token)
        if(self.level == 0 and len(self.other_tokens) == 0) :
            # NOTE : Logic to change base-level tokens to 'desc', as is defined in backend spec...
            self.major_token = 'desc'
        elif(self.level < 0) :
            raise TokenException("Attempted to go deeper into a max-depth token: @" + '-'.join(self.prev_tokens) + 
                                    '-' if len(self.prev_tokens > 0) else '' + "[" + self.major_token + "].")
        else :
            self.major_token = self.other_tokens[0]
            self.other_tokens = self.other_tokens[1:]
        return self
    
    def __str__(self) :
        return("(" + 
               ",".join([str(self.level), str(self.lineno), self.major_token, "-".join(self.other_tokens), self.body]) +
               ")")

filename = "pdam_cunning.MEDFORD"
tokens = Token.generate_tokens(filename)
print(Token.get_major_tokens(tokens))